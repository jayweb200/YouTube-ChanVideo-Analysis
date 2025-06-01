import json
import os
import hashlib
import pandas as pd
import google.generativeai as genai
from sklearn.preprocessing import MinMaxScaler # For normalization

# --- Configuration ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Replace with your actual key

# --- Purple Cow Context ---
PURPLE_COW_CONTEXT = """
The "Purple Cow" concept, coined by Seth Godin, emphasizes the importance of creating products, services, or, in this case, content that is truly remarkable.
A Purple Cow stands out from the herd of brown cows. It's something exceptional, new, and exciting that people can't help but notice and talk about.
In the context of YouTube, a "Purple Cow" video isn't just good; it's different, counter-intuitive, surprising, or outrageous in a way that grabs attention and sparks conversation.

Key Principles for "Purple Cow" YouTube Content:
1.  **Be Remarkable:** Don't be boring. Create content that is worth talking about.
2.  **Niche Down (then Dominate):** Find a specific audience or topic area where you can be the go-to, unique voice.
3.  **Challenge Norms:** Question assumptions. Do the opposite of what everyone else is doing if it creates value or intrigue.
4.  **Solve Problems Uniquely:** If you're solving a problem, do it in a way no one else has thought of, or address a problem no one else is.
5.  **Embrace Controversy (Carefully):** Well-handled controversial or contrarian views can be remarkable. This requires tact and a strong understanding of your audience.
6.  **Exceptional Value or Entertainment:** Provide value or entertainment that is significantly better or different than the alternatives.
7.  **Target a Specific Audience:** Design your content for a specific group that will get excited about it and share it.
8.  **Iterate on What Works (but don't become a brown cow):** Once you find a "Purple Cow," explore its variations, but always be on the lookout for the next one. Don't let your Purple Cow become just another brown cow through repetition.

The goal is not to appeal to everyone, but to create something that a specific group of people will love and share passionately.
For YouTube, this means titles that are irresistible, thumbnails that demand clicks, and content that delivers on the promise in an unforgettable way.
"""

# --- Function Definitions ---

def load_video_data(json_path="youtube_video_data.json"):
    """Loads the video data from the specified JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Video data loaded successfully from {json_path}")
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        return None

def select_top_videos(video_data_list, num_videos=10):
    """
    Selects top videos based on a scoring mechanism (retention and shares).
    """
    if not video_data_list:
        print("No video data provided to select_top_videos.")
        return []

    # Create a DataFrame for easier manipulation
    df = pd.DataFrame(video_data_list)

    # Ensure required columns exist
    if 'retention_rate' not in df.columns or 'shares' not in df.columns:
        print("Warning: 'retention_rate' or 'shares' column missing. Returning empty list.")
        return []

    # Handle None values by filling with 0 for scoring purposes
    df['retention_rate'] = pd.to_numeric(df['retention_rate'], errors='coerce').fillna(0)
    df['shares'] = pd.to_numeric(df['shares'], errors='coerce').fillna(0)

    # Normalize 'retention_rate' and 'shares' (Min-Max Scaling)
    scaler = MinMaxScaler()
    # Avoid scaling if all values are the same (e.g., all zeros)
    if len(df['retention_rate'].unique()) > 1:
        df['normalized_retention'] = scaler.fit_transform(df[['retention_rate']])
    else:
        df['normalized_retention'] = 0.0 if len(df) > 0 else df['retention_rate']


    if len(df['shares'].unique()) > 1:
        df['normalized_shares'] = scaler.fit_transform(df[['shares']])
    else:
        df['normalized_shares'] = 0.0 if len(df) > 0 else df['shares']

    # Calculate score
    df['score'] = (0.6 * df['normalized_retention']) + (0.4 * df['normalized_shares'])

    # Sort by score and select top N
    top_videos_df = df.sort_values(by='score', ascending=False).head(num_videos)

    print(f"Selected {len(top_videos_df)} top videos based on retention and shares.")
    return top_videos_df.to_dict('records')


def extract_topics_themes_with_gemini(video_title, video_description, gemini_model):
    """
    Extracts topics and themes from video title and description using Gemini.
    Includes basic file-based caching.
    """
    cache_dir = "topic_cache"
    os.makedirs(cache_dir, exist_ok=True)

    # Create a unique cache key (hash of title and description)
    # Using description as well to make it more unique for videos with similar titles
    cache_input = f"{video_title}_{video_description}"
    cache_key = hashlib.md5(cache_input.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    # Check cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                print(f"Loading cached topic analysis for: {video_title[:50]}...")
                return json.load(f)
        except Exception as e:
            print(f"Cache read error for {video_title[:50]}: {e}. Re-fetching.")

    prompt = f'''
Analyze the following YouTube video title and description to identify its core content.
Provide the output as a JSON object with the following keys:
- "primary_topic": A concise phrase for the main subject.
- "secondary_topics": A list of 2-4 secondary subjects or keywords.
- "overall_theme": A short sentence describing the overarching theme or message.
- "content_category": Suggest a broad content category (e.g., "Educational", "Entertainment", "Review", "Tutorial", "Vlog").

Title: "{video_title}"
Description: "{video_description if video_description else 'No description provided.'}"

Return ONLY the JSON object. Ensure the JSON is valid.
'''
    default_error_response = {
        "primary_topic": "Error in extraction",
        "secondary_topics": [],
        "overall_theme": "Could not determine theme due to error.",
        "content_category": "Unknown"
    }

    try:
        print(f"Extracting topics for: {video_title[:50]}... (using Gemini)")
        response = gemini_model.generate_content(prompt)

        # Clean response: remove potential markdown backticks and leading/trailing whitespace
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        analysis = json.loads(cleaned_response_text)

        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

        return analysis
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error for '{video_title[:50]}': {e}")
        print(f"Gemini raw response was: {response.text[:200]}...") # Log part of the raw response
        return default_error_response
    except Exception as e:
        print(f"Error extracting topics for '{video_title[:50]}' with Gemini: {e}")
        return default_error_response

def generate_content_plan_with_gemini(top_video_analyses, purple_cow_context, gemini_model, num_ideas=5):
    """
    Generates a content plan with new video ideas using Gemini, based on top video analysis and Purple Cow strategy.
    """
    if not top_video_analyses:
        print("No top video analyses provided to generate content plan.")
        return []

    # Summarize the successful content
    primary_topics = [analysis.get('primary_topic', 'N/A') for analysis in top_video_analyses if analysis]
    categories = [analysis.get('content_category', 'N/A') for analysis in top_video_analyses if analysis]
    # Filter out "Error in extraction" or similar default error messages
    successful_topics_summary = ", ".join(set(pt for pt in primary_topics if pt not in ["Error in extraction", "N/A"]))
    successful_categories_summary = ", ".join(set(cat for cat in categories if cat not in ["Unknown", "N/A"]))

    # Example titles from successful videos (if available and not error states)
    example_titles = [analysis.get('original_title', '') for analysis in top_video_analyses if analysis and 'original_title' in analysis and analysis.get('primary_topic') != "Error in extraction"]
    example_titles_summary = ""
    if example_titles:
        example_titles_summary = f" achieving high engagement with content like \"{'; '.join(example_titles[:2])}\"."


    channel_success_summary = (
        f"This channel has found success with videos primarily about [{successful_topics_summary if successful_topics_summary else 'various topics'}] "
        f"in the [{successful_categories_summary if successful_categories_summary else 'diverse'}] category{example_titles_summary}"
    )

    prompt = f"""
You are an expert YouTube content strategist specializing in creating viral 'Purple Cow' content.
Your task is to generate {num_ideas} new, unique, and remarkable video ideas for a YouTube channel.

First, understand the "Purple Cow" concept:
{purple_cow_context}

Now, consider the channel's existing successful content:
{channel_success_summary}

Based on this, generate {num_ideas} video ideas. Each idea must embody the "Purple Cow" principles – it should be remarkable, not just a variation of existing content unless that variation itself is remarkable.
For each idea, provide:
- "title": A catchy, attention-grabbing title in the Purple Cow style.
- "description": 1-3 sentences explaining the video concept, what it will cover, and what makes it remarkable or a "Purple Cow".

Return the ideas as a JSON list of objects. Each object should have a "title" and "description" key.
Example format:
[
  {{ "title": "Idea 1 Title", "description": "Description for Idea 1..." }},
  {{ "title": "Idea 2 Title", "description": "Description for Idea 2..." }}
]

Ensure the JSON is valid. Focus on novelty and the Purple Cow principles.
The ideas should be distinct from one another and push creative boundaries while remaining relevant to potential audience interests hinted at by past successes.
"""

    try:
        print(f"Generating {num_ideas} Purple Cow content ideas with Gemini...")
        response = gemini_model.generate_content(prompt)

        # Clean response: remove potential markdown backticks and leading/trailing whitespace
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        content_ideas = json.loads(cleaned_response_text)
        print(f"Successfully generated {len(content_ideas)} content ideas.")
        return content_ideas
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error while generating content plan: {e}")
        print(f"Gemini raw response was: {response.text[:500]}...")
        return []
    except Exception as e:
        print(f"Error generating content plan with Gemini: {e}")
        return []

def save_plan_to_markdown(content_plan, top_analyzed_videos_summary, filepath="content_plan.md"):
    """Saves the generated content plan to a Markdown file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# YouTube Content Strategy: The Purple Cow Plan\n\n")

            f.write("## Analysis of Top Performing Content (Inspiration)\n\n")
            if top_analyzed_videos_summary:
                for i, analysis in enumerate(top_analyzed_videos_summary):
                    original_title = analysis.get('original_title', 'Unknown Title')
                    primary_topic = analysis.get('primary_topic', 'N/A')
                    theme = analysis.get('overall_theme', 'N/A')
                    category = analysis.get('content_category', 'N/A')
                    f.write(f"### Top Video: \"{original_title}\"\n")
                    f.write(f"- **Primary Topic:** {primary_topic}\n")
                    f.write(f"- **Overall Theme:** {theme}\n")
                    f.write(f"- **Content Category:** {category}\n\n")
            else:
                f.write("No top video analyses were available to summarize.\n\n")

            f.write("## Generated 'Purple Cow' Video Ideas\n\n")
            if content_plan:
                for i, idea in enumerate(content_plan):
                    f.write(f"### Idea {i+1}: {idea.get('title', 'No Title Provided')}\n")
                    f.write(f"{idea.get('description', 'No description provided.')}\n\n")
            else:
                f.write("No content ideas were generated.\n")

        print(f"Content plan saved successfully to {filepath}")
    except Exception as e:
        print(f"Error saving content plan to Markdown: {e}")

# --- Main Execution ---
def main():
    """Main function to orchestrate the content planning process."""
    print("Starting content planner script...")

    # Configure Gemini
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}. Please ensure GEMINI_API_KEY is set correctly.")
        return

    # 1. Load video data
    video_data_container = load_video_data()
    if not video_data_container or 'videos' not in video_data_container:
        print("Failed to load video data or data is not in expected format. Exiting.")
        return

    all_videos = video_data_container['videos']

    # 2. Select top videos
    # Ensure 'description' is carried over or default to empty string if not present
    for video in all_videos:
        if 'description' not in video: # Assuming description might be missing from raw data
            video['description'] = ""
    top_videos = select_top_videos(all_videos, num_videos=5) # Analyze top 5 for now

    if not top_videos:
        print("No top videos selected. Cannot proceed with analysis. Exiting.")
        return

    # 3. Extract topics and themes from top videos
    top_video_analyses = []
    print("\n--- Extracting Topics from Top Videos ---")
    for video in top_videos:
        # Make sure description exists, default to empty if not
        description = video.get('description', '')
        analysis = extract_topics_themes_with_gemini(video['title'], description, gemini_model)
        analysis['original_title'] = video['title'] # Keep original title for summary
        top_video_analyses.append(analysis)

    # 4. Generate content plan
    print("\n--- Generating Content Plan ---")
    content_ideas = generate_content_plan_with_gemini(top_video_analyses, PURPLE_COW_CONTEXT, gemini_model, num_ideas=7)

    # 5. Save plan to Markdown
    if content_ideas:
        save_plan_to_markdown(content_ideas, top_video_analyses, filepath="content_plan.md")
    else:
        print("No content ideas were generated, so no plan will be saved.")

    print("\nContent planner script finished.")

if __name__ == "__main__":
    main()
