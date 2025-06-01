# YouTube Channel Video Analysis

This repository contains a collection of Python scripts for analyzing YouTube channel performance, generating media kits, and extracting insights from video data.

## Features

- Extract comprehensive data from your YouTube channel
- Analyze video performance metrics (views, engagement, retention)
- Generate media kits for potential sponsors
- Analyze video titles and thumbnails using AI
- Identify patterns in successful content

## Prerequisites

- Python 3.6+
- Google account with access to YouTube Analytics
- Google Cloud Platform project with YouTube Data API v3 and YouTube Analytics API enabled
- OpenAI API key (for AI-powered analysis features, if using older versions or specific scripts)
- Gemini API key (for AI-powered analysis features using Google's Gemini models)

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/youtube-channel-video-analysis.git
cd youtube-channel-video-analysis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up authentication

#### YouTube API Authentication

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3 and YouTube Analytics API
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type
   - Add "http://localhost:8080" as an authorized redirect URI
   - Click "Create"
5. Download the credentials JSON file
6. Rename the downloaded file to `credentials.json` and place it in the project root directory

Alternatively, you can copy the `credentials.json.example` file, rename it to `credentials.json`, and fill in your credentials:

```json
{
    "web": {
      "client_id": "YOUR_CLIENT_ID_HERE",
      "project_id": "YOUR_PROJECT_ID_HERE",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_secret": "YOUR_CLIENT_SECRET_HERE",
      "redirect_uri": ["http://localhost:YOUR_PORT_HERE/"],
      "flowName": ["GeneralOAuthFlow"]
    }
}
```

#### OpenAI API Authentication (for AI analysis features)

1. Sign up for an OpenAI API key at [OpenAI's website](https://openai.com/api/)
2. In the analysis scripts (`analyze.py`, `analyze_new.py`, `analyze_new_json.py`), replace the placeholder API key with your actual key:

```python
API_KEY = "your_openai_api_key_here"
```

#### Gemini API Authentication (for AI analysis features)

1. Obtain your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) or the Google Cloud Console.
2. In the analysis scripts (`analyze.py`, `analyze_new.py`, `analyze_new_json.py`), replace the placeholder `GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"` with your actual key:

```python
GEMINI_API_KEY = "your_gemini_api_key_here"
```

## Usage

### Extract YouTube Channel Data

```bash
python get_data.py
```

This will:
- Authenticate with your YouTube account
- Extract data for your latest 50 videos
- Save the data to `youtube_video_data.json` and `youtube_video_data.csv`
- Generate a basic performance analysis in `video_performance_analysis.txt`

### Generate a Media Kit

```bash
python media.py
```

This will:
- Create a comprehensive media kit with channel statistics
- Save the data to `youtube_media_kit.json`
- Generate a human-readable summary in `youtube_media_kit_summary.txt`

### Analyze Videos with AI

```bash
python analyze.py
```

This will:
- Analyze your top 10 videos by views
- Use AI models (like Google Gemini) to analyze titles and thumbnails
- Generate insights about what makes your content successful
- Save the analysis to `youtube_analysis_results.json` and `youtube_analysis_report.md`

## Security Notes

- **IMPORTANT**: Never commit your `credentials.json` or `token.json` files to public repositories
- These files contain sensitive authentication information
- The `.gitignore` file is configured to exclude these files
- If you're forking this repository, make sure to set up your own credentials

## License

[MIT License](LICENSE)
