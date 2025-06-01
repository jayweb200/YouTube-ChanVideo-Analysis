#!/usr/bin/env python3
"""
YouTube Media Kit Generator

This script generates a comprehensive media kit for your YouTube channel
in JSON format with all the statistics and demographics that sponsors
and advertisers typically look for.
"""

import os
import json
import pandas as pd
import argparse
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Authentication scopes needed for YouTube API access
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def get_authenticated_service():
    """
    Authenticates with YouTube API using OAuth 2.0 credentials.
    Returns authenticated YouTube API and YouTube Analytics API service objects.
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
                # Use a fixed port (8080) instead of dynamic port
                creds = flow.run_local_server(port=8080)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        # Build both YouTube Data API and YouTube Analytics API service objects
        youtube = build('youtube', 'v3', credentials=creds)
        youtube_analytics = build('youtubeAnalytics', 'v2', credentials=creds)
        
        return youtube, youtube_analytics
    except Exception as e:
        print(f"YouTube authentication failed: {str(e)}")
        raise


def get_channel_info(youtube, target_channel_id):
    """
    Retrieves comprehensive channel information for the specified channel ID.
    """
    try:
        channels_request = youtube.channels().list(
            part="id,snippet,statistics,brandingSettings,contentDetails,topicDetails",
            id=target_channel_id
        )
        channel_response = channels_request.execute()
        
        if 'items' not in channel_response or len(channel_response['items']) == 0:
            raise Exception(f"No channel found with ID: {target_channel_id}")
        
        channel = channel_response['items'][0]
        
        # Extract relevant channel information
        channel_info = {
            'id': channel['id'],
            'title': channel['snippet']['title'],
            'description': channel['snippet']['description'],
            'customUrl': channel['snippet'].get('customUrl', ''),
            'publishedAt': channel['snippet']['publishedAt'],
            'thumbnails': channel['snippet']['thumbnails'],
            'country': channel['snippet'].get('country', 'Unknown'),
            'viewCount': int(channel['statistics'].get('viewCount', 0)),
            'subscriberCount': int(channel['statistics'].get('subscriberCount', 0)),
            'hiddenSubscriberCount': channel['statistics'].get('hiddenSubscriberCount', False),
            'videoCount': int(channel['statistics'].get('videoCount', 0)),
            'keywords': channel.get('brandingSettings', {}).get('channel', {}).get('keywords', '')
        }
        
        return channel_info
    except Exception as e:
        print(f"Error retrieving channel info for {target_channel_id}: {str(e)}")
        raise


def get_channel_demographics(youtube_analytics, target_channel_id): # Add target_channel_id here
    """
    Retrieves demographic information about the channel's audience.
    """
    try:
        # Get the current date and a date 90 days ago
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Initialize response variables
        demographics_response = {"rows": []}
        geography_response = {"rows": []}
        device_response = {"rows": []}
        
        try:
            # Get viewer demographics by age and gender
            demographics_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date,
                endDate=end_date,
                metrics="viewerPercentage",
                dimensions="ageGroup,gender",
                sort="gender,ageGroup"
            )
            demographics_response = demographics_request.execute()
            print("Successfully retrieved age and gender demographics")
        except Exception as e:
            print(f"Could not retrieve age and gender demographics: {str(e)}")
        
        try:
            # Get viewer demographics by geography (countries)
            # Using views instead of viewerPercentage for better compatibility
            geography_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date,
                endDate=end_date,
                metrics="views",
                dimensions="country",
                sort="-views",
                maxResults=25
            )
            geography_response = geography_request.execute()
            print("Successfully retrieved country demographics")
        except Exception as e:
            print(f"Could not retrieve country demographics: {str(e)}")
        
        try:
            # Get viewer demographics by device type
            device_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date,
                endDate=end_date,
                metrics="views",
                dimensions="deviceType",
                sort="-views"
            )
            device_response = device_request.execute()
            print("Successfully retrieved device demographics")
        except Exception as e:
            print(f"Could not retrieve device demographics: {str(e)}")
        
        # Process and format the demographic data
        demographics = {
            'ageGender': {},
            'countries': {},
            'devices': {}
        }
        
        # Process age and gender data
        if 'rows' in demographics_response:
            for row in demographics_response['rows']:
                gender = row[1]
                age_group = row[0]
                percentage = row[2]
                
                if gender not in demographics['ageGender']:
                    demographics['ageGender'][gender] = {}
                
                demographics['ageGender'][gender][age_group] = percentage
        
        # Process country data
        if 'rows' in geography_response:
            # Calculate total views for percentage calculation
            total_country_views = sum(row[1] for row in geography_response['rows'])
            
            for row in geography_response['rows']:
                country = row[0]
                views = row[1]
                # Calculate percentage from views
                percentage = (views / total_country_views * 100) if total_country_views > 0 else 0
                demographics['countries'][country] = percentage
        
        # Process device data
        if 'rows' in device_response:
            total_views = sum(row[1] for row in device_response.get('rows', []))
            for row in device_response.get('rows', []):
                device_type = row[0]
                views = row[1]
                percentage = (views / total_views * 100) if total_views > 0 else 0
                demographics['devices'][device_type] = {
                    'views': views,
                    'percentage': percentage
                }
        
        return demographics
    except Exception as e:
        print(f"Error retrieving demographics: {str(e)}")
        # Return empty demographics if there's an error
        return {
            'ageGender': {},
            'countries': {},
            'devices': {}
        }


def get_performance_metrics(youtube_analytics, target_channel_id):
    """
    Retrieves overall channel performance metrics for the specified channel ID.
    """
    try:
        # Get current date and format properly
        now = datetime.now()
        end_date = now.strftime('%Y-%m-%d')
        
        # For monthly dimension, start date must be the first day of a month
        first_day_current_month = datetime(now.year, now.month, 1)
        start_date_30d = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        start_date_90d = (now - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # For year to date, use January 1st of current year
        start_date_ytd = datetime(now.year, 1, 1).strftime('%Y-%m-%d')
        
        # For monthly data, go back 12 months but align to first day of month
        twelve_months_ago = first_day_current_month.replace(year=first_day_current_month.year - 1)
        start_date_monthly = twelve_months_ago.strftime('%Y-%m-%d')
        
        print(f"Performance date ranges: 30d({start_date_30d}), 90d({start_date_90d}), YTD({start_date_ytd}), Monthly({start_date_monthly})")
        
        # Initialize response variables with default empty data
        metrics_30d_response = {"rows": [[0, 0, 0, 0, 0, 0, 0]]}
        metrics_90d_response = {"rows": [[0, 0, 0, 0, 0, 0, 0]]}
        metrics_ytd_response = {"rows": [[0, 0, 0, 0, 0, 0, 0]]}
        monthly_data_response = {"rows": []}
        watch_percentage_response = {"rows": [[0]]}
        
        try:
            # Get 30-day metrics
            metrics_30d_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date_30d,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares"
            )
            metrics_30d_response = metrics_30d_request.execute()
            print("Successfully retrieved 30-day metrics")
        except Exception as e:
            print(f"Could not retrieve 30-day metrics: {str(e)}")
        
        try:
            # Get 90-day metrics
            metrics_90d_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date_90d,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares"
            )
            metrics_90d_response = metrics_90d_request.execute()
            print("Successfully retrieved 90-day metrics")
        except Exception as e:
            print(f"Could not retrieve 90-day metrics: {str(e)}")
        
        try:
            # Get year-to-date metrics
            metrics_ytd_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date_ytd,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments,shares"
            )
            metrics_ytd_response = metrics_ytd_request.execute()
            print("Successfully retrieved year-to-date metrics")
        except Exception as e:
            print(f"Could not retrieve year-to-date metrics: {str(e)}")
        
        try:
            # Get monthly data for growth chart - ensuring dates align with month boundaries
            monthly_data_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date_monthly,
                endDate=end_date,
                metrics="views,subscribersGained",
                dimensions="month",
                sort="month"
            )
            monthly_data_response = monthly_data_request.execute()
            print("Successfully retrieved monthly growth data")
        except Exception as e:
            print(f"Could not retrieve monthly growth data: {str(e)}")
        
        try:
            # Get average watch percentage
            watch_percentage_request = youtube_analytics.reports().query(
                ids=f"channel=={target_channel_id}",
                startDate=start_date_90d,
                endDate=end_date,
                metrics="averageViewPercentage"
            )
            watch_percentage_response = watch_percentage_request.execute()
            print("Successfully retrieved average view percentage")
        except Exception as e:
            watch_percentage_response = {"rows": [[0]]}
            print(f"Could not retrieve average view percentage: {str(e)}")
        
        # Process the metrics data
        performance = {
            'last30Days': {},
            'averages': {}
        }
        
        # Extract values from the 30-day metrics
        if 'rows' in metrics_30d_response and metrics_30d_response['rows']:
            row = metrics_30d_response['rows'][0]
            performance['last30Days'] = {
                'views': row[0],
                'watchTimeMinutes': row[1],
                'avgViewDuration': row[2],
                'subscribersGained': row[3],
                'likes': row[4],
                'comments': row[5],
                'shares': row[6]
            }
        
        # We're removing the 90-day metrics, year-to-date metrics, and monthly growth data as requested
        
        # Calculate average watch percentage
        if 'rows' in watch_percentage_response and watch_percentage_response['rows']:
            performance['averages']['averageViewPercentage'] = watch_percentage_response['rows'][0][0]
        
        # Calculate additional averages
        if performance['last30Days'] and 'views' in performance['last30Days']:
            performance['averages']['dailyViews'] = round(performance['last30Days']['views'] / 30)
            performance['averages']['viewsPerVideo'] = 0  # Will be calculated later with video count
            
            if performance['last30Days']['views'] > 0:
                performance['averages']['engagementRate'] = round(
                    (performance['last30Days']['likes'] + performance['last30Days']['comments']) / 
                    performance['last30Days']['views'] * 100, 2
                )
        
        return performance
    except Exception as e:
        print(f"Error retrieving performance metrics: {str(e)}")
        # Return empty performance metrics if there's an error
        return {
            'last30Days': {},
            'last90Days': {},
            'lastYear': {},
            'monthlyGrowth': [],
            'averages': {}
        }


def get_top_videos(youtube, channel_info):
    """
    Retrieves information about the channel's last 10 published videos.
    """
    try:
        # Get the upload playlist ID from the channel's contentDetails
        channels_request = youtube.channels().list(
            part="contentDetails",
            id=channel_info['id']
        )
        channel_response = channels_request.execute()
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get all videos from the uploads playlist
        videos = []
        next_page_token = None
        
        # We'll get all videos but limit to processing the top 50 for the media kit
        max_results_per_request = 50
        max_total_videos = 50
        
        while True:
            # Get playlist items (videos)
            playlist_items_request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=max_results_per_request,
                pageToken=next_page_token
            )
            playlist_items_response = playlist_items_request.execute()
            
            # Extract video IDs
            video_ids = [item['contentDetails']['videoId'] for item in playlist_items_response.get('items', [])]
            
            if video_ids:
                # Get detailed video information
                videos_request = youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=','.join(video_ids)
                )
                videos_response = videos_request.execute()
                
                # Add videos to our list
                for video in videos_response.get('items', []):
                    video_data = {
                        'id': video['id'],
                        'title': video['snippet']['title'],
                        'publishedAt': video['snippet']['publishedAt'],
                        'thumbnails': video['snippet']['thumbnails'],
                        'viewCount': int(video['statistics'].get('viewCount', 0)),
                        'likeCount': int(video['statistics'].get('likeCount', 0)),
                        'commentCount': int(video['statistics'].get('commentCount', 0)),
                        'duration': video['contentDetails']['duration']
                    }
                    videos.append(video_data)
            
            next_page_token = playlist_items_response.get('nextPageToken')
            
            # Break the loop if there are no more pages or we have enough videos
            if not next_page_token or len(videos) >= max_total_videos:
                break
        
        # Sort videos by publish date (newest first)
        videos.sort(key=lambda x: x['publishedAt'], reverse=True)
        last_10_videos = videos[:10]  # Keep only last 10 videos published
        
        # Calculate average views for the last 10 videos
        if last_10_videos:
            avg_views = sum(video['viewCount'] for video in last_10_videos) / len(last_10_videos)
        else:
            avg_views = 0
        
        return {
            'topVideos': last_10_videos,
            'averageViews': avg_views
        }
    except Exception as e:
        print(f"Error retrieving top videos: {str(e)}")
        return {
            'topVideos': [],
            'averageViews': 0
        }


def create_media_kit(target_channel_id, output_json_filename, output_summary_filename):
    """
    Creates a comprehensive media kit for the specified channel ID.
    Saves the kit to the provided filenames.
    """
    try:
        print(f"Authenticating with YouTube API for channel: {target_channel_id}...")
        youtube, youtube_analytics = get_authenticated_service()
        
        media_kit = {
            'generatedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '_channel_id_arg': target_channel_id, # For error case partial save
            'channelInfo': {},
            'audience': {
                'ageGender': {},
                'countries': {},
                'devices': {}
            },
            'performance': {
                'last30Days': {},
                'averages': {}
            },
            'topContent': {
                'topVideos': [],
                'averageViews': 0
            }
        }
        
        try:
            print(f"Retrieving channel information for {target_channel_id}...")
            channel_info = get_channel_info(youtube, target_channel_id)
            media_kit['channelInfo'] = channel_info
        except Exception as e:
            print(f"Error retrieving channel info for {target_channel_id}: {str(e)}")
        
        try:
            print(f"Retrieving audience demographics for {target_channel_id}...")
            demographics = get_channel_demographics(youtube_analytics, target_channel_id)
            media_kit['audience'] = demographics
        except Exception as e:
            print(f"Error retrieving demographics for {target_channel_id}: {str(e)}")
        
        try:
            print(f"Retrieving performance metrics for {target_channel_id}...")
            performance = get_performance_metrics(youtube_analytics, target_channel_id)
            media_kit['performance'] = performance
        except Exception as e:
            print(f"Error retrieving performance metrics for {target_channel_id}: {str(e)}")
        
        try:
            print("Retrieving top videos...")
            if 'channelInfo' in media_kit and media_kit['channelInfo']:
                videos_data = get_top_videos(youtube, media_kit['channelInfo'])
                media_kit['topContent'] = videos_data
                
                # Update average views per video in performance metrics
                if 'averages' in media_kit['performance']:
                    media_kit['performance']['averages']['viewsPerVideo'] = videos_data['averageViews']
            else:
                print("Skipping top videos retrieval as channel info is not available")
        except Exception as e:
            print(f"Error retrieving top videos: {str(e)}")
        
        # Save to JSON file
        # Save to JSON file
        with open(output_json_filename, 'w', encoding='utf-8') as f:
            json.dump(media_kit, f, ensure_ascii=False, indent=2)
        
        print(f"Media kit successfully generated and saved to {output_json_filename}")
        
        # Also create a summary text file with key metrics
        create_summary_text(media_kit, output_summary_filename)
        
        return media_kit
    except Exception as e:
        print(f"Error creating media kit for {target_channel_id}: {str(e)}")
        
        # Even if there was an error, try to save whatever data we have
        try:
            partial_media_kit = {
                'generatedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'note': "This is a partial media kit due to errors during generation"
            }
            
            # Add any data that might have been collected before the error
            if 'media_kit' in locals():
                partial_media_kit.update(media_kit)
            
            # Save the partial media kit
            # Use channel_id if available, otherwise a generic name
            partial_filename = f'youtube_media_kit_partial_{target_channel_id}.json'

            with open(partial_filename, 'w', encoding='utf-8') as f:
                json.dump(partial_media_kit, f, ensure_ascii=False, indent=2)
            
            print(f"Saved partial media kit data to {partial_filename}")
            return partial_media_kit
        except:
            print("Could not save partial media kit data")
            return None


def create_summary_text(media_kit, output_summary_file):
    """
    Creates a human-readable summary of the media kit.
    """
    try:
        channel = media_kit.get('channelInfo', {})
        performance = media_kit.get('performance', {})
        audience = media_kit.get('audience', {})
        top_content = media_kit.get('topContent', {})
        
        summary = f"YOUTUBE CHANNEL MEDIA KIT SUMMARY\n"
        summary += f"Generated on: {media_kit.get('generatedAt', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n\n"
        
        # Channel info
        summary += f"CHANNEL INFORMATION\n"
        summary += f"Name: {channel.get('title', 'N/A')}\n"
        
        if 'id' in channel:
            summary += f"URL: https://www.youtube.com/channel/{channel['id']}\n"
        else:
            summary += f"URL: N/A\n"
            
        summary += f"Custom URL: {channel.get('customUrl', 'None')}\n"
        summary += f"Subscribers: {channel.get('subscriberCount', 0):,}\n"
        summary += f"Total Videos: {channel.get('videoCount', 0)}\n"
        summary += f"Total Views: {channel.get('viewCount', 0):,}\n"
        
        if 'publishedAt' in channel:
            try:
                created_date = datetime.strptime(channel['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')
            except:
                created_date = channel['publishedAt']
            summary += f"Created: {created_date}\n\n"
        else:
            summary += f"Created: N/A\n\n"
        
        # Performance metrics
        summary += f"PERFORMANCE METRICS (LAST 30 DAYS)\n"
        if 'last30Days' in performance and performance['last30Days']:
            last30 = performance['last30Days']
            summary += f"Views: {int(last30.get('views', 0)):,}\n"
            summary += f"Watch Time: {int(last30.get('watchTimeMinutes', 0)):,} minutes\n"
            summary += f"Avg. View Duration: {int(last30.get('avgViewDuration', 0)):,} seconds\n"
            summary += f"New Subscribers: {int(last30.get('subscribersGained', 0)):,}\n"
            summary += f"Likes: {int(last30.get('likes', 0)):,}\n"
            summary += f"Comments: {int(last30.get('comments', 0)):,}\n\n"
        else:
            summary += f"Views: 0\n"
            summary += f"Watch Time: 0 minutes\n"
            summary += f"Avg. View Duration: 0 seconds\n"
            summary += f"New Subscribers: 0\n"
            summary += f"Likes: 0\n"
            summary += f"Comments: 0\n\n"
        
        # Averages
        summary += f"CHANNEL AVERAGES\n"
        if 'averages' in performance:
            avgs = performance['averages']
            summary += f"Daily Views: {avgs.get('dailyViews', 0):,}\n"
            summary += f"Views Per Video: {int(avgs.get('viewsPerVideo', 0)):,}\n"
            summary += f"Engagement Rate: {avgs.get('engagementRate', 0)}%\n"
            summary += f"Average View Percentage: {avgs.get('averageViewPercentage', 0)}%\n\n"
        
        # Audience demographics
        summary += f"AUDIENCE DEMOGRAPHICS\n"
        
        # Gender and age
        if 'ageGender' in audience and audience['ageGender']:
            summary += "Gender & Age:\n"
            for gender, age_data in audience['ageGender'].items():
                summary += f"  {gender}: "
                age_items = []
                for age, percentage in age_data.items():
                    age_items.append(f"{age}: {percentage:.1f}%")
                summary += ", ".join(age_items) + "\n"
            summary += "\n"
        
        # Top countries
        if 'countries' in audience and audience['countries']:
            summary += "Top Countries:\n"
            sorted_countries = sorted(audience['countries'].items(), key=lambda x: x[1], reverse=True)
            for country, percentage in sorted_countries[:5]:
                summary += f"  {country}: {percentage:.1f}%\n"
            summary += "\n"
        
        # Devices
        if 'devices' in audience and audience['devices']:
            summary += "Device Types:\n"
            for device, data in audience['devices'].items():
                summary += f"  {device}: {data.get('percentage', 0):.1f}%\n"
            summary += "\n"
        
        # Top videos
        summary += f"TOP 5 VIDEOS\n"
        for i, video in enumerate(top_content.get('topVideos', [])[:5], 1):
            summary += f"{i}. \"{video['title']}\"\n"
            summary += f"   Views: {video['viewCount']:,}\n"
            summary += f"   Likes: {video['likeCount']:,}\n"
            summary += f"   URL: https://www.youtube.com/watch?v={video['id']}\n"
        
        # Save summary to file
        with open(output_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"Media kit summary saved to {output_summary_file}")
    except Exception as e:
        print(f"Error creating summary text: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a YouTube Media Kit.")
    parser.add_argument("--channel_id", type=str, required=True, help="The YouTube Channel ID for which to generate the media kit.")
    parser.add_argument("--data_file", type=str, required=True, help="Path to the input JSON data file (e.g., youtube_video_data_CHANNELID.json). Note: This script currently fetches most data live; this argument is for consistency but primarily uses channel_id for API calls.")
    args = parser.parse_args()

    print("YouTube Media Kit Generator")
    print("===========================")
    print(f"Generating media kit for Channel ID: {args.channel_id}")
    print(f"Using data file (primarily for reference, most data fetched live): {args.data_file}")

    # Define output filenames based on channel_id
    output_json_file = f"youtube_media_kit_{args.channel_id}.json"
    output_summary_file = f"youtube_media_kit_summary_{args.channel_id}.txt"

    # Pass these filenames and channel_id to create_media_kit, perhaps via a config dict or directly
    # For simplicity, I'll modify create_media_kit to accept them or fetch from a passed config
    # For now, I'll add them to a dictionary that create_media_kit can use,
    # and pass channel_id directly where needed for API calls.

    # The create_media_kit function will be modified to accept channel_id for API calls
    # and use these filenames.

    media_kit_data = create_media_kit(
        target_channel_id=args.channel_id,
        output_json_filename=output_json_file,
        output_summary_filename=output_summary_file
    ) # This function signature will need to be updated
    
    if media_kit_data:
        print("\nMedia Kit Creation Complete!")
        print("\nFiles created:")
        print(f"1. {output_json_file} - Complete media kit data in JSON format")
        print(f"2. {output_summary_file} - Human-readable summary of key metrics")
    else:
        print("\nMedia Kit Creation Failed or was incomplete.")
    
    print("\nNext steps:")
    print("1. Use the JSON file to build your custom media kit UI")
    print("2. Run this script periodically to keep your media kit updated")
