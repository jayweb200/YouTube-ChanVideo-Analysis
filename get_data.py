#!/usr/bin/env python3
"""
YouTube Channel Analytics Extractor for LLM Analysis

This script extracts comprehensive data from your latest 50 YouTube videos
to help analyze patterns in topics, titles, thumbnails, and performance metrics.
The output is formatted for easy analysis with Large Language Models (LLMs).
"""

import os
import pandas as pd
import json
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from fastapi import HTTPException

# Authentication scopes needed for YouTube API access
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def analyze_video_performance(video_data):
    """
    Performs basic analysis on video performance to identify patterns.
    This serves as a starting point for LLM analysis.
    
    Args:
        video_data: List of video data dictionaries
        
    Returns:
        String containing analysis report
    """
    if not video_data:
        return "No video data available for analysis."
    
    # Sort videos by different metrics
    by_views = sorted(video_data, key=lambda x: x['views'], reverse=True)
    by_engagement = sorted(video_data, key=lambda x: x['engagement_rate'], reverse=True)
    
    # Filter videos with valid retention rate
    videos_with_retention = [v for v in video_data if v['retention_rate'] is not None]
    by_retention = sorted(videos_with_retention, key=lambda x: x['retention_rate'], reverse=True) if videos_with_retention else []
    
    # Calculate average performance metrics
    avg_views = sum(video['views'] for video in video_data) / len(video_data) if video_data else 0
    avg_engagement = sum(video['engagement_rate'] for video in video_data) / len(video_data) if video_data else 0
    avg_retention = sum(v['retention_rate'] for v in videos_with_retention) / len(videos_with_retention) if videos_with_retention else 0
    
    # Build analysis report
    report = "VIDEO PERFORMANCE ANALYSIS\n"
    report += "=" * 50 + "\n\n"
    
    # Top performing videos
    report += "TOP PERFORMING VIDEOS BY VIEWS:\n"
    for i, video in enumerate(by_views[:5], 1):
        report += f"{i}. \"{video['title']}\" - {video['views']} views\n"
    
    report += "\nTOP PERFORMING VIDEOS BY ENGAGEMENT RATE:\n"
    for i, video in enumerate(by_engagement[:5], 1):
        report += f"{i}. \"{video['title']}\" - {video['engagement_rate']}% engagement\n"
    
    if by_retention:
        report += "\nTOP PERFORMING VIDEOS BY VIEWER RETENTION:\n"
        for i, video in enumerate(by_retention[:5], 1):
            report += f"{i}. \"{video['title']}\" - {video['retention_rate']}% retention\n"
    
    # Content patterns
    report += "\n\nCONTENT PATTERNS:\n"
    report += f"Average views per video: {int(avg_views)}\n"
    report += f"Average engagement rate: {avg_engagement:.2f}%\n"
    if videos_with_retention:
        report += f"Average retention rate: {avg_retention:.2f}%\n"
    
    # Title length analysis
    title_lengths = [len(video['title']) for video in video_data]
    avg_title_length = sum(title_lengths) / len(title_lengths) if title_lengths else 0
    
    title_word_counts = [len(video['title'].split()) for video in video_data]
    avg_title_words = sum(title_word_counts) / len(title_word_counts) if title_word_counts else 0
    
    report += f"\nAverage title length: {avg_title_length:.1f} characters, {avg_title_words:.1f} words\n"
    
    # Duration analysis
    report += "\nNOTE: This is a basic analysis. For deeper insights, provide this data to an LLM along with specific questions about content strategy."
    
    return report


def format_duration_for_humans(seconds):
    """
    Convert seconds to a human-readable format (MM:SS or HH:MM:SS)
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds is None or not isinstance(seconds, (int, float)):
        return "N/A"
        
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def get_authenticated_service():
    """
    Authenticates with YouTube API using OAuth 2.0 credentials.
    Returns authenticated YouTube API service object and YouTube Analytics API service object.
    """
    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Use a fixed port (8080) instead of dynamic port (0)
                creds = flow.run_local_server(port=8080)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        # Build both YouTube Data API and YouTube Analytics API service objects
        youtube = build('youtube', 'v3', credentials=creds)
        youtube_analytics = build('youtubeAnalytics', 'v2', credentials=creds)
        
        return youtube, youtube_analytics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"YouTube authentication failed: {str(e)}"
        )


def get_channel_id(youtube):
    """
    Retrieves the authenticated user's channel ID.
    """
    request = youtube.channels().list(
        part="id",
        mine=True
    )
    response = request.execute()
    
    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['id']
    else:
        raise Exception("Could not retrieve channel ID")


def get_latest_videos(youtube, channel_id, max_results=50):
    """
    Retrieves the latest videos from the specified channel with detailed information.
    
    Args:
        youtube: Authenticated YouTube API service object
        channel_id: YouTube channel ID
        max_results: Maximum number of videos to retrieve (default: 50)
        
    Returns:
        List of video items with detailed information
    """
    # First get the list of video IDs
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=max_results,
        order="date",
        type="video"
    )
    response = request.execute()
    
    # Extract video IDs
    video_ids = [item['id']['videoId'] for item in response.get('items', [])]
    
    # Get detailed video information - request more parts for detailed data
    if video_ids:
        videos_request = youtube.videos().list(
            part="snippet,statistics,contentDetails,status",
            id=','.join(video_ids)
        )
        return videos_request.execute()['items']
    
    return []


def get_video_analytics(youtube_analytics, video_id, published_at_str):
    """
    Retrieves analytics data for a specific video.
    Metrics: averageViewDuration, shares, subscribersGained, subscribersLost
    Date range: From video publish date to current date.
    """
    try:
        # Parse published_at_str (ISO 8601 format, e.g., '2023-10-26T14:00:00Z')
        # Convert to 'YYYY-MM-DD' format
        start_date_dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        start_date = start_date_dt.strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        # Ensure start_date is not after end_date (can happen for very new videos or clock sync issues)
        if start_date > end_date:
            start_date = end_date

        report_request = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="averageViewDuration,shares,subscribersGained,subscribersLost",
            dimensions="video",
            filters=f"video=={video_id}"
        )
        response = report_request.execute()
        
        avg_duration = None
        shares = None
        subscribers_gained = None
        subscribers_lost = None
        
        if 'rows' in response and response['rows']:
            row = response['rows'][0]
            # Order of metrics in response matches the query: video_id, avgViewDuration, shares, subsGained, subsLost
            # row[0] is video_id (dimension)
            avg_duration = row[1] if len(row) > 1 else None
            shares = row[2] if len(row) > 2 else None
            subscribers_gained = row[3] if len(row) > 3 else None
            subscribers_lost = row[4] if len(row) > 4 else None

        return {
            'avg_view_duration': avg_duration,
            'shares': shares,
            'subscribers_gained': subscribers_gained,
            'subscribers_lost': subscribers_lost
        }
    except Exception as e:
        print(f"Could not retrieve extended analytics for video {video_id}: {str(e)}")
        return {
            'avg_view_duration': None,
            'shares': None,
            'subscribers_gained': None,
            'subscribers_lost': None
        }


def parse_duration(duration_str):
    """
    Parse ISO 8601 duration string into human-readable format.
    Example: PT1H30M15S -> 1:30:15
    """
    duration = duration_str.replace('PT', '')
    hours = 0
    minutes = 0
    seconds = 0
    
    if 'H' in duration:
        hours, duration = duration.split('H')
        hours = int(hours)
    
    if 'M' in duration:
        minutes, duration = duration.split('M')
        minutes = int(minutes)
    
    if 'S' in duration:
        seconds = int(duration.replace('S', ''))
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def extract_video_data(youtube, youtube_analytics):
    """
    Main function to extract video data from the authenticated user's channel.
    Gathers comprehensive data suitable for LLM analysis of content patterns.
    """
    try:
        # Get channel ID
        channel_id = get_channel_id(youtube)
        print(f"Found channel ID: {channel_id}")
        
        # Get channel info
        channel_request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        channel_response = channel_request.execute()
        channel_info = channel_response['items'][0]
        channel_name = channel_info['snippet']['title']
        subscriber_count = channel_info['statistics']['subscriberCount']
        
        print(f"Channel: {channel_name}")
        print(f"Subscribers: {subscriber_count}")
        
        # Get latest videos
        videos = get_latest_videos(youtube, channel_id)
        print(f"Retrieved {len(videos)} videos")
        
        # Extract and organize video data
        video_data = []
        
        for video in videos:
            video_id = video['id']
            snippet = video['snippet']
            statistics = video['statistics']
            content_details = video.get('contentDetails', {})
            
            # Get best thumbnail (highest resolution available)
            thumbnails = snippet['thumbnails']
            thumbnail_url = thumbnails.get('maxres', thumbnails.get('high', thumbnails.get('medium', thumbnails.get('default'))))['url']
            
            # Get analytics data
            analytics = get_video_analytics(youtube_analytics, video_id, snippet['publishedAt'])
            
            # Format video duration
            iso_duration = content_details.get('duration', 'PT0S')
            duration = parse_duration(iso_duration)
            
            # Calculate engagement rates
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            engagement_rate = 0
            if view_count > 0:
                engagement_rate = ((like_count + comment_count) / view_count) * 100
            
            # Convert averageViewDuration to human-readable format if available
            avg_view_duration_seconds = analytics.get('avg_view_duration')
            avg_view_duration_formatted = format_duration_for_humans(avg_view_duration_seconds)
            
            # Calculate viewer retention if both durations are available
            retention_rate = None
            if avg_view_duration_seconds is not None and isinstance(avg_view_duration_seconds, (int, float)):
                # Convert ISO duration to seconds
                total_seconds = 0
                duration_str = iso_duration.replace('PT', '')
                
                if 'H' in duration_str:
                    hours, duration_str = duration_str.split('H')
                    total_seconds += int(hours) * 3600
                
                if 'M' in duration_str:
                    minutes, duration_str = duration_str.split('M')
                    total_seconds += int(minutes) * 60
                
                if 'S' in duration_str:
                    seconds = duration_str.replace('S', '')
                    total_seconds += int(seconds)
                
                if total_seconds > 0:
                    retention_rate = (avg_view_duration_seconds / total_seconds) * 100
            
            # Create video data entry with comprehensive information
            video_entry = {
                'title': snippet['title'],
                'video_id': video_id,
                'published_at': snippet['publishedAt'],
                'thumbnail_url': thumbnail_url,
                'duration': duration,
                'views': view_count,
                'likes': like_count,
                'comments': comment_count,
                'engagement_rate': round(engagement_rate, 2),
                'avg_view_duration_seconds': avg_view_duration_seconds,
                'avg_view_duration': avg_view_duration_formatted,
                'retention_rate': round(retention_rate, 2) if retention_rate is not None else None,
                'shares': analytics.get('shares', 0) if analytics.get('shares') is not None else 0,
                'subscribers_gained': analytics.get('subscribers_gained', 0) if analytics.get('subscribers_gained') is not None else 0,
                'subscribers_lost': analytics.get('subscribers_lost', 0) if analytics.get('subscribers_lost') is not None else 0
            }
            
            video_data.append(video_entry)
        
        # Create DataFrame for CSV export
        df = pd.DataFrame(video_data)
        
        # Format the date for better readability
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Sort by publication date (newest first)
        df = df.sort_values(by='published_at', ascending=False)
        
        # Save to CSV
        output_file_csv = 'youtube_video_data.csv'
        df.to_csv(output_file_csv, index=False)
        
        # Save full data to JSON
        output_file_json = 'youtube_video_data.json'
        with open(output_file_json, 'w', encoding='utf-8') as f:
            json.dump({
                'channel': {
                    'name': channel_name,
                    'id': channel_id,
                    'subscribers': subscriber_count
                },
                'videos': video_data,
                'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, ensure_ascii=False, indent=2)
        
        print(f"Data successfully exported to {output_file_csv} and {output_file_json}")
        
        # Simple performance analysis
        performance_analysis = analyze_video_performance(video_data)
        
        # Save analysis to a separate file
        output_analysis_file = 'video_performance_analysis.txt'
        with open(output_analysis_file, 'w', encoding='utf-8') as f:
            f.write(performance_analysis)
        
        print(f"Performance analysis saved to {output_analysis_file}")
        
        return df, video_data
    
    except Exception as e:
        print(f"Error extracting video data: {str(e)}")
        raise


if __name__ == "__main__":
    youtube, youtube_analytics = get_authenticated_service()
    video_data_df, video_data_full = extract_video_data(youtube, youtube_analytics)
    
    # Display summary
    print("\nSUMMARY:")
    print(f"Total videos extracted: {len(video_data_df)}")
    
    if not video_data_df.empty:
        # Most viewed video
        if 'views' in video_data_df and video_data_df['views'].max() > 0:
            print(f"Most viewed video: {video_data_df.loc[video_data_df['views'].idxmax()]['title']}")
        
        # Most liked video
        if 'likes' in video_data_df and video_data_df['likes'].max() > 0:
            print(f"Most liked video: {video_data_df.loc[video_data_df['likes'].idxmax()]['title']}")
        
        # Most engaging video
        if 'engagement_rate' in video_data_df:
            print(f"Most engaging video: {video_data_df.loc[video_data_df['engagement_rate'].idxmax()]['title']}")
    
    print("\nFiles created:")
    print("1. youtube_video_data.csv - Basic video data in CSV format")
    print("2. youtube_video_data.json - Comprehensive video data including comments in JSON format")
    print("3. video_performance_analysis.txt - Basic performance analysis")
    
    print("\nNEXT STEPS:")
    print("1. Upload these files to an LLM conversation")
    print("2. Ask the LLM specific questions about your content strategy")
    print("3. For example:")
    print("   - What patterns do you see in my most successful videos?")
    print("   - What topics should I focus on for future videos?")
    print("   - How can I improve my titles and thumbnails?")
    print("   - What content length works best for my audience?")
