import json
import os
import requests
from io import BytesIO
import pandas as pd
from openai import OpenAI

from PIL import Image
from urllib.request import urlopen
import matplotlib.pyplot as plt
import seaborn as sns

API_KEY = "sk-XXX"


# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

def load_data(json_file_path):
    """Load YouTube data from JSON file"""
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def get_top_videos(data, metric='views', count=10):
    """Get top videos based on specified metric"""
    videos = data['videos']
    df = pd.DataFrame(videos)
    
    # Convert views to numeric if not already
    if df[metric].dtype == 'object':
        df[metric] = pd.to_numeric(df[metric])
    
    # Sort by the chosen metric and get top N
    top_videos = df.sort_values(by=metric, ascending=False).head(count)
    return top_videos

def analyze_title_with_llm(title):
    """Analyze title using OpenAI's GPT model"""
    # Check if we already have a cached title analysis
    cache_dir = "title_analysis_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create a cache filename based on a hash of the title
    import hashlib
    title_hash = hashlib.md5(title.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{title_hash}.txt")
    
    # Check if analysis is already cached
    if os.path.exists(cache_file):
        print(f"Loading cached title analysis for '{title}'")
        with open(cache_file, 'r') as f:
            return f.read()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert in YouTube content strategy and SEO. Analyze this video title and identify key patterns and elements that make it effective. Focus on psychological triggers, keywords, structure, emotion, and clarity."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this YouTube title and explain why it's effective: \"{title}\""
                }
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        analysis = response.choices[0].message.content
        
        # Cache the result
        with open(cache_file, 'w') as f:
            f.write(analysis)
            
        return analysis
    except Exception as e:
        print(f"Error analyzing title with LLM: {e}")
        return "Error analyzing title"

def analyze_thumbnail_with_vision(thumbnail_url):
    """Analyze thumbnail using OpenAI's Vision model"""
    # Check if we already have a cached thumbnail analysis
    cache_dir = "thumbnail_analysis_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create a cache filename based on the video ID (extracted from URL)
    video_id = thumbnail_url.split('/')[-2] if '/vi/' in thumbnail_url else thumbnail_url.split('/')[-1].split('.')[0]
    cache_file = os.path.join(cache_dir, f"{video_id}.txt")
    
    # Check if analysis is already cached
    if os.path.exists(cache_file):
        print(f"Loading cached thumbnail analysis for {video_id}")
        with open(cache_file, 'r') as f:
            return f.read()
    
    try:
        # Get image data
        response = requests.get(thumbnail_url)
        if response.status_code != 200:
            return "Failed to retrieve thumbnail image"
        
        # Send to OpenAI Vision
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in YouTube thumbnail analysis. Examine this thumbnail and identify key elements that make it effective. Focus on composition, colors, text usage, emotional triggers, and clickability factors."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this YouTube thumbnail and explain why it's effective:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": thumbnail_url,
                            },
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        analysis = response.choices[0].message.content
        
        # Cache the result
        with open(cache_file, 'w') as f:
            f.write(analysis)
            
        return analysis
    except Exception as e:
        print(f"Error analyzing thumbnail with Vision: {e}")
        return "Error analyzing thumbnail"

def get_combined_analysis(row):
    """Combined analysis of title and thumbnail with additional video metrics"""
    
    print(f"Analyzing {row['title']} ({row['video_id']})...")
    
    # Get video metrics
    metrics_analysis = f"""
VIDEO METRICS:
- Views: {row['views']}
- Likes: {row['likes']}
- Comments: {row['comments']}
- Engagement Rate: {row['engagement_rate']}%
- Avg View Duration: {row['avg_view_duration']} ({row['retention_rate']}% retention)
- Published: {row['published_at']}
    """
    
    # Analyze title with GPT
    title_analysis = analyze_title_with_llm(row['title'])
    
    # Analyze thumbnail with Vision
    thumbnail_analysis = analyze_thumbnail_with_vision(row['thumbnail_url'])
    
    # Combine all analyses
    combined_analysis = f"""
=== ANALYSIS FOR VIDEO: {row['title']} ===
{metrics_analysis}

TITLE ANALYSIS:
{title_analysis}

THUMBNAIL ANALYSIS:
{thumbnail_analysis}

VIDEO URL: https://www.youtube.com/watch?v={row['video_id']}
==========================================================
    """
    
    return combined_analysis

def generate_patterns_report(all_analyses):
    """Generate a report of common patterns across top videos using GPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert in YouTube content strategy. Based on the analyses of multiple top-performing videos, identify common patterns, success factors, and actionable recommendations. Be specific and detailed in your analysis."
                },
                {
                    "role": "user", 
                    "content": f"Here are analyses of top-performing YouTube videos. Identify common patterns, success factors, and provide actionable recommendations:\n\n{all_analyses}"
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating patterns report: {e}")
        return "Error generating patterns report"

def save_intermediate_results(data, video_analyses, top_videos, step="video_analysis"):
    """Save intermediate results to avoid repeating analysis if there's an error later"""
    intermediate_results = {
        'channel_name': data['channel']['name'],
        'channel_subscribers': data['channel']['subscribers'],
        'video_analyses': video_analyses,
        'analysis_step': step,
        'top_videos': top_videos.to_dict('records') if isinstance(top_videos, pd.DataFrame) else top_videos
    }
    
    # Save to JSON file
    with open('youtube_analysis_intermediate.json', 'w') as f:
        json.dump(intermediate_results, f, indent=2)
    
    print(f"Intermediate results saved after '{step}' step")

def load_intermediate_results():
    """Load intermediate results if they exist"""
    try:
        with open('youtube_analysis_intermediate.json', 'r') as f:
            results = json.load(f)
        return results
    except Exception as e:
        print(f"No intermediate results found: {e}")
        return None

def create_final_report(data, video_analyses, patterns_report, top_videos=None):
    """Create the final markdown report"""
    # Save full results
    results = {
        'channel_name': data['channel']['name'],
        'channel_subscribers': data['channel']['subscribers'],
        'video_analyses': video_analyses,
        'patterns_report': patterns_report
    }
    
    # Save to JSON file
    with open('youtube_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save human-readable report to text file
    with open('youtube_analysis_report.md', 'w') as f:
        f.write(f"# YouTube Content Analysis for {data['channel']['name']}\n\n")
        f.write(f"Channel Subscribers: {data['channel']['subscribers']}\n\n")
        f.write("## Top 10 Videos by Views\n\n")
        
        # If we have the top_videos DataFrame
        if isinstance(top_videos, pd.DataFrame):
            for idx, (_, row) in enumerate(top_videos.iterrows()):
                f.write(f"{idx+1}. **{row['title']}** - {row['views']} views\n")
        # If we have the list from intermediate results
        elif top_videos is not None:
            for idx, video in enumerate(top_videos):
                f.write(f"{idx+1}. **{video['title']}** - {video['views']} views\n")
        # If we don't have a list, use the analyses
        else:
            sorted_videos = sorted(video_analyses.values(), key=lambda x: x['views'], reverse=True)
            for idx, video in enumerate(sorted_videos):
                f.write(f"{idx+1}. **{video['title']}** - {video['views']} views\n")
        
        f.write("\n## Video Analyses\n\n")
        for analysis in video_analyses.values():
            f.write(f"### {analysis['title']} ({analysis['views']} views)\n\n")
            f.write(analysis['analysis'].replace("===", "").replace("===", ""))
            f.write("\n---\n\n")
        
        f.write("## Patterns & Recommendations\n\n")
        f.write(patterns_report)
    
    print("Analysis complete!")
    print("Results saved to 'youtube_analysis_results.json'")
    print("Report saved to 'youtube_analysis_report.md'")

def main():
    # Check for intermediate results first
    intermediate = load_intermediate_results()
    
    if intermediate and intermediate.get('analysis_step') == "video_analysis":
        print("Found intermediate results from previous video analysis run")
        print("Skipping individual video analysis and proceeding to pattern analysis")
        
        # Get data from intermediate results
        data = {'channel': {'name': intermediate['channel_name'], 'subscribers': intermediate['channel_subscribers']}}
        video_analyses = intermediate['video_analyses']
        top_videos = intermediate['top_videos']
        
        # Build all_analyses string from video_analyses
        all_analyses = ""
        for video_id, analysis_data in video_analyses.items():
            all_analyses += analysis_data['analysis'] + "\n\n"
        
    else:
        # Start from the beginning
        print("No intermediate results found or results are incomplete. Starting from scratch.")
        
        # Load the JSON data
        data_path = "youtube_video_data.json"  # Update with your file path if needed
        data = load_data(data_path)
        
        if not data:
            print("Failed to load data. Exiting.")
            return
        
        # Get top 10 videos by views
        top_videos = get_top_videos(data, metric='views', count=10)
        print(f"Found {len(top_videos)} top videos by views.")
        
        # Analyze each video's title and thumbnail
        all_analyses = ""
        video_analyses = {}
        
        for idx, (_, row) in enumerate(top_videos.iterrows()):
            print(f"Analyzing video {idx+1} of {len(top_videos)}...")
            analysis = get_combined_analysis(row)
            
            # Store analysis
            video_analyses[row['video_id']] = {
                'title': row['title'],
                'views': row['views'],
                'analysis': analysis
            }
            
            all_analyses += analysis + "\n\n"
            
            # Save intermediate results after each video
            save_intermediate_results(data, video_analyses, top_videos, "video_analysis")
    
    # Generate overall patterns report
    print("Generating patterns report...")
    patterns_report = generate_patterns_report(all_analyses)
    
    # Create final report
    create_final_report(data, video_analyses, patterns_report, top_videos)

def analyze_videos_only():
    """Run only the video analysis part without generating patterns"""
    # Load the JSON data
    data_path = "youtube_video_data.json"
    data = load_data(data_path)
    
    if not data:
        print("Failed to load data. Exiting.")
        return
    
    # Get top 10 videos by views
    top_videos = get_top_videos(data, metric='views', count=10)
    print(f"Found {len(top_videos)} top videos by views.")
    
    # Analyze each video's title and thumbnail
    video_analyses = {}
    
    for idx, (_, row) in enumerate(top_videos.iterrows()):
        print(f"Analyzing video {idx+1} of {len(top_videos)}...")
        analysis = get_combined_analysis(row)
        
        # Store analysis
        video_analyses[row['video_id']] = {
            'title': row['title'],
            'views': row['views'],
            'analysis': analysis
        }
        
        # Save intermediate results after each video
        save_intermediate_results(data, video_analyses, top_videos, "video_analysis")
    
    print("Video analysis complete! Run the script with --patterns flag to generate the patterns report.")

def analyze_patterns_only():
    """Run only the patterns analysis using saved video analyses"""
    # Check for intermediate results
    intermediate = load_intermediate_results()
    
    if not intermediate or intermediate.get('analysis_step') != "video_analysis":
        print("No intermediate video analysis results found. Run the script with --videos flag first.")
        return
    
    # Get data from intermediate results
    data = {'channel': {'name': intermediate['channel_name'], 'subscribers': intermediate['channel_subscribers']}}
    video_analyses = intermediate['video_analyses']
    top_videos = intermediate['top_videos']
    
    # Build all_analyses string from video_analyses
    all_analyses = ""
    for video_id, analysis_data in video_analyses.items():
        all_analyses += analysis_data['analysis'] + "\n\n"
    
    # Generate overall patterns report
    print("Generating patterns report...")
    patterns_report = generate_patterns_report(all_analyses)
    
    # Create final report
    create_final_report(data, video_analyses, patterns_report, top_videos)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze YouTube video data')
    parser.add_argument('--videos', action='store_true', help='Run only video analysis')
    parser.add_argument('--patterns', action='store_true', help='Run only patterns analysis')
    
    args = parser.parse_args()
    
    if args.videos:
        analyze_videos_only()
    elif args.patterns:
        analyze_patterns_only()
    else:
        main()