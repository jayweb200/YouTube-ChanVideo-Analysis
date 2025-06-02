import json
import os
import requests
from io import BytesIO
import pandas as pd
import google.generativeai as genai
import argparse
import time

from PIL import Image
from urllib.request import urlopen
import matplotlib.pyplot as plt
import seaborn as sns


GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini models
models = {
    'text': genai.GenerativeModel('gemini-pro'),
    'vision': genai.GenerativeModel('gemini-pro-vision')
}

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
    """Analyze title using Gemini"""
    try:
        prompt = f"You are an expert in YouTube content strategy and SEO. Analyze this video title and identify key patterns and elements that make it effective. Focus on psychological triggers, keywords, structure, emotion, and clarity. Analyze this YouTube title and explain why it's effective: \"{title}\""
        response = models['text'].generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error analyzing title with LLM: {e}")
        return "Error analyzing title"

def analyze_thumbnail_with_vision(thumbnail_url):
    """Analyze thumbnail using Gemini Vision model"""
    try:
        # Get image data
        image_response = requests.get(thumbnail_url)
        if image_response.status_code != 200:
            return "Failed to retrieve thumbnail image"
        
        image_bytes = image_response.content
        image_part = {
            "mime_type": "image/jpeg",  # Assuming JPEG, adjust if necessary
            "data": image_bytes
        }

        prompt_parts = [
            "You are an expert in YouTube thumbnail analysis. Examine this thumbnail and identify key elements that make it effective. Focus on composition, colors, text usage, emotional triggers, and clickability factors.",
            "Analyze this YouTube thumbnail and explain why it's effective:",
            image_part
        ]
        
        response = models['vision'].generate_content(prompt_parts)
        return response.text
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
    """Generate a report of common patterns across top videos using Gemini"""
    try:
        prompt = f"You are an expert in YouTube content strategy. Based on the analyses of multiple top-performing videos, identify common patterns, success factors, and actionable recommendations. Be specific and detailed in your analysis. Here are analyses of top-performing YouTube videos. Identify common patterns, success factors, and provide actionable recommendations:\n\n{all_analyses}"
        response = models['text'].generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating patterns report: {e}")
        return "Error generating patterns report"

def main():
    parser = argparse.ArgumentParser(description="Analyze YouTube video data using AI models.")
    parser.add_argument("--data_file", type=str, required=True, help="Path to the input YouTube video data JSON file (e.g., youtube_video_data_CHANNELID.json).")
    parser.add_argument("--channel_id", type=str, required=True, help="Channel ID to be used for naming output files.")
    args = parser.parse_args()

    print(f"Starting analysis for channel {args.channel_id} using data from: {args.data_file}")

    # Load the JSON data
    data = load_data(args.data_file)
    
    if not data:
        print(f"Failed to load data from {args.data_file}. Exiting.")
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

        # Add delay here, before processing the next video
        if idx < len(top_videos) - 1: # Avoid sleep after the last video
            print(f"Processed video {idx+1}/{len(top_videos)}. Waiting 2 seconds before next API call...")
            time.sleep(2)
    
    # Generate overall patterns report
    print("Generating patterns report...")
    patterns_report = generate_patterns_report(all_analyses)
    
    # Save results
    results = {
        'channel_name': data['channel']['name'],
        'channel_subscribers': data['channel']['subscribers'],
        'video_analyses': video_analyses,
        'patterns_report': patterns_report
    }
    
    # Save to JSON file
    output_json_file = f"youtube_analysis_results_{args.channel_id}.json"
    with open(output_json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save human-readable report to text file
    output_report_file = f"youtube_analysis_report_{args.channel_id}.md"
    with open(output_report_file, 'w') as f:
        f.write(f"# YouTube Content Analysis for {data['channel']['name']}\n\n")
        f.write(f"Channel Subscribers: {data['channel']['subscribers']}\n\n")
        f.write("## Top 10 Videos by Views\n\n")
        
        for idx, (_, row) in enumerate(top_videos.iterrows()):
            f.write(f"{idx+1}. **{row['title']}** - {row['views']} views\n")
        
        f.write("\n## Video Analyses\n\n")
        for analysis in video_analyses.values():
            f.write(f"### {analysis['title']} ({analysis['views']} views)\n\n")
            f.write(analysis['analysis'].replace("===", "").replace("===", ""))
            f.write("\n---\n\n")
        
        f.write("## Patterns & Recommendations\n\n")
        f.write(patterns_report)
    
    print("Analysis complete!")
    print(f"Results saved to '{output_json_file}'")
    print(f"Report saved to '{output_report_file}'")

if __name__ == "__main__":
    main()