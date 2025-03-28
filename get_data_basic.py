#!/usr/bin/env python3
"""
YouTube Channel Analytics Extractor

This script extracts data for the latest 50 videos from your YouTube channel
including title, thumbnail, views, publish date, likes, CTR, and view duration.
"""

import os
import pandas as pd
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
    Retrieves the latest videos from the specified channel.
    
    Args:
        youtube: Authenticated YouTube API service object
        channel_id: YouTube channel ID
        max_results: Maximum number of videos to retrieve (default: 50)
        
    Returns:
        List of video items
    """
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
    
    # Get detailed video information
    if video_ids:
        videos_request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=','.join(video_ids)
        )
        return videos_request.execute()['items']
    
    return []


def get_video_analytics(youtube_analytics, video_id):
    """
    Retrieves analytics data (average view duration) for a specific video.
    
    Note: YouTube Analytics API has limitations on how far back you can retrieve data.
    """
    try:
        # Get the current date and a date 30 days ago
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get view duration (average watch time)
        duration_request = youtube_analytics.reports().query(
            ids=f"channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="averageViewDuration",
            dimensions="video",
            filters=f"video=={video_id}"
        )
        duration_response = duration_request.execute()
        
        # Extract value
        avg_duration = None
        
        if 'rows' in duration_response and duration_response['rows']:
            avg_duration = duration_response['rows'][0][1]
        
        return {
            'avg_view_duration': avg_duration
        }
    except Exception as e:
        # Return default values if analytics cannot be retrieved
        print(f"Could not retrieve analytics for video {video_id}: {str(e)}")
        # Return default values and continue with the script instead of failing
        return {
            'avg_view_duration': None
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
    """
    try:
        # Get channel ID
        channel_id = get_channel_id(youtube)
        print(f"Found channel ID: {channel_id}")
        
        # Get latest videos
        videos = get_latest_videos(youtube, channel_id)
        print(f"Retrieved {len(videos)} videos")
        
        # Extract and organize video data
        video_data = []
        
        for video in videos:
            video_id = video['id']
            snippet = video['snippet']
            statistics = video['statistics']
            
            # Get best thumbnail (highest resolution available)
            thumbnails = snippet['thumbnails']
            thumbnail_url = thumbnails.get('maxres', thumbnails.get('high', thumbnails.get('medium', thumbnails.get('default'))))['url']
            
            # Get analytics data
            analytics = get_video_analytics(youtube_analytics, video_id)
            
            # Format video duration
            content_details = video.get('contentDetails', {})
            duration = parse_duration(content_details.get('duration', 'PT0S'))
            
            # Create video data entry
            video_entry = {
                'title': snippet['title'],
                'video_id': video_id,
                'published_at': snippet['publishedAt'],
                'thumbnail_url': thumbnail_url,
                'views': int(statistics.get('viewCount', 0)),
                'likes': int(statistics.get('likeCount', 0)),
                'video_duration': duration,
                'avg_view_duration': analytics['avg_view_duration'] if analytics['avg_view_duration'] is not None else "N/A"
            }
            
            video_data.append(video_entry)
        
        # Create DataFrame and export to CSV
        df = pd.DataFrame(video_data)
        
        # Format the date for better readability
        df['published_at'] = pd.to_datetime(df['published_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Sort by publication date (newest first)
        df = df.sort_values(by='published_at', ascending=False)
        
        # Save to CSV
        output_file = 'youtube_video_data.csv'
        df.to_csv(output_file, index=False)
        
        print(f"Data successfully exported to {output_file}")
        return df
    
    except Exception as e:
        print(f"Error extracting video data: {str(e)}")
        raise


if __name__ == "__main__":
    youtube, youtube_analytics = get_authenticated_service()
    video_data = extract_video_data(youtube, youtube_analytics)
    
    # Display summary
    print("\nSUMMARY:")
    print(f"Total videos extracted: {len(video_data)}")
    
    if not video_data.empty:
        # Most viewed video
        if 'views' in video_data and video_data['views'].max() > 0:
            print(f"Most viewed video: {video_data.loc[video_data['views'].idxmax()]['title']}")
        
        # Most liked video
        if 'likes' in video_data and video_data['likes'].max() > 0:
            print(f"Most liked video: {video_data.loc[video_data['likes'].idxmax()]['title']}")
        
        # Analytics data summaries - only if data is available and numeric
        if 'avg_view_duration' in video_data and video_data['avg_view_duration'].apply(lambda x: isinstance(x, (int, float))).any():
            duration_data = video_data[video_data['avg_view_duration'].apply(lambda x: isinstance(x, (int, float)))]
            if not duration_data.empty:
                print(f"Video with longest avg view duration: {duration_data.loc[duration_data['avg_view_duration'].idxmax()]['title']}")
    
    print("\nNOTE: To see analytics data (average view duration), please enable the YouTube Analytics API in your Google Cloud Console.")