# YouTube Channel Video Analysis

This repository contains a collection of Python scripts for analyzing YouTube channel performance, generating media kits, and extracting insights from video data.

## Features

- Extract comprehensive data from your YouTube channel
- Analyze video performance metrics (views, engagement, retention)
- Generate media kits for potential sponsors
- Analyze video titles and thumbnails using AI
- Identify patterns in successful content
- Generate new content ideas using AI and strategic marketing principles (Purple Cow)

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

#### Finding Your YouTube Channel ID
For channel-specific analysis and operations, you'll need your YouTube Channel ID (it usually starts with 'UC').
You can find your Channel ID in YouTube Studio:
1. Go to YouTube Studio.
2. In the left sidebar, click on "Settings".
3. In the Settings popup, go to "Channel" -> "Advanced settings".
4. Scroll down, and you should see your "YouTube Channel ID".

Alternatively, if you are on your channel's page, you can often find it in the URL (e.g., `https://www.youtube.com/channel/YOUR_CHANNEL_ID`).

## Usage

**Important Workflow Note:**
Most scripts now operate on a specific channel's data. The general workflow is:
1. Run `python get_data.py --channel_id YOUR_CHANNEL_ID_HERE` to fetch data for your channel. This will create files like `youtube_video_data_YOUR_CHANNEL_ID.json`.
2. Use this generated `youtube_video_data_YOUR_CHANNEL_ID.json` file as input (`--data_file`) for other scripts like `analyze.py`, `analyze_new.py`, `analyze_new_json.py`, and `content_planner.py`.
3. Always provide the same `--channel_id YOUR_CHANNEL_ID_HERE` to these subsequent scripts so they can correctly name their output files.

### Extract YouTube Channel Data

```bash
python get_data.py --channel_id YOUR_CHANNEL_ID_HERE
```

- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) Replace `YOUR_CHANNEL_ID_HERE` with the actual ID of the YouTube channel you want to analyze.

This will:
- Authenticate with your YouTube account (if it's the first run or token expired).
- Extract data for the latest 50 videos from the specified channel.
- Save the data to channel-specific files:
    - `youtube_video_data_YOUR_CHANNEL_ID.csv`
    - `youtube_video_data_YOUR_CHANNEL_ID.json`
- Generate a basic performance analysis in `video_performance_analysis_YOUR_CHANNEL_ID.txt`.

### Generate a Media Kit

```bash
python media.py --channel_id YOUR_CHANNEL_ID_HERE --data_file youtube_video_data_YOUR_CHANNEL_ID.json
```

- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) The ID of the YouTube channel for which to generate the media kit. This ID is also used for naming the output files.
- **`--data_file youtube_video_data_YOUR_CHANNEL_ID.json`**: (Required) Path to the channel-specific data file. While `media.py` fetches most data live via APIs using the authenticated user's context for the given channel ID, this argument is included for command-line consistency. Ensure the channel ID in the filename matches the `--channel_id` argument.

This will:
- Create a comprehensive media kit with channel statistics for the specified channel.
- Save the data to channel-specific files:
    - `youtube_media_kit_YOUR_CHANNEL_ID.json`
    - `youtube_media_kit_summary_YOUR_CHANNEL_ID.txt`

### Analyze Videos with AI (`analyze.py`)

```bash
python analyze.py --data_file youtube_video_data_YOUR_CHANNEL_ID.json --channel_id YOUR_CHANNEL_ID_HERE
```

- **`--data_file youtube_video_data_YOUR_CHANNEL_ID.json`**: (Required) Path to the channel-specific JSON data file generated by `get_data.py`.
- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) The Channel ID, used for naming the output files.

This will:
- Analyze the top 10 videos (by views) from the provided data file.
- Use AI models (like Google Gemini) to analyze titles and thumbnails.
- Generate insights about what makes your content successful.
- Save the analysis to channel-specific files:
    - `youtube_analysis_results_YOUR_CHANNEL_ID.json`
    - `youtube_analysis_report_YOUR_CHANNEL_ID.md`

### Advanced AI Analysis with Caching (`analyze_new.py`)

```bash
python analyze_new.py --data_file youtube_video_data_YOUR_CHANNEL_ID.json --channel_id YOUR_CHANNEL_ID_HERE
```

- **`--data_file youtube_video_data_YOUR_CHANNEL_ID.json`**: (Required) Path to the channel-specific JSON data file.
- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) The Channel ID, used for naming output and intermediate files.
- Optional flags: `--videos` (run only video analysis), `--patterns` (run only pattern analysis from cached video analysis).

This script offers advanced analysis features, including caching of AI results to save costs on re-runs.
- Output files (channel-specific):
    - `youtube_analysis_results_YOUR_CHANNEL_ID.json`
    - `youtube_analysis_report_YOUR_CHANNEL_ID.md`
    - Intermediate cache files in `title_analysis_cache/` and `thumbnail_analysis_cache/`.
    - Intermediate results file: `youtube_analysis_intermediate_YOUR_CHANNEL_ID.json`.

### Structured JSON AI Analysis (`analyze_new_json.py`)

```bash
python analyze_new_json.py --data_file youtube_video_data_YOUR_CHANNEL_ID.json --channel_id YOUR_CHANNEL_ID_HERE
```

- **`--data_file youtube_video_data_YOUR_CHANNEL_ID.json`**: (Required) Path to the channel-specific JSON data file.
- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) The Channel ID, used for naming output and intermediate files.
- Optional flags: `--videos`, `--patterns`.

Similar to `analyze_new.py` but focuses on generating more structured JSON output suitable for UIs or further automated processing.
- Output files (channel-specific):
    - `youtube_analysis_results_YOUR_CHANNEL_ID.json` (backward compatible)
    - `youtube_analysis_ui_YOUR_CHANNEL_ID.json` (structured JSON for UI)
    - `youtube_analysis_report_YOUR_CHANNEL_ID.md`
    - Intermediate cache files and `youtube_analysis_intermediate_YOUR_CHANNEL_ID.json`.

### Generate a Content Plan with AI (Purple Cow Strategy)

```bash
python content_planner.py --data_file youtube_video_data_YOUR_CHANNEL_ID.json --channel_id YOUR_CHANNEL_ID_HERE
```

- **`--data_file youtube_video_data_YOUR_CHANNEL_ID.json`**: (Required) Path to the channel-specific JSON data file.
- **`--channel_id YOUR_CHANNEL_ID_HERE`**: (Required) The Channel ID, used for naming the output file.

This script uses the "Purple Cow" marketing strategy (inspired by Seth Godin) along with AI analysis of your top-performing videos (based on retention and shares from the input file) to suggest novel content ideas.
- **Output**: The script will generate a channel-specific content plan: `content_plan_YOUR_CHANNEL_ID.md`.
- **Dependencies**: This feature uses `scikit-learn` for data normalization (included in `requirements.txt`).
- Caches topic analysis in `topic_cache/`.

## Security Notes

- **IMPORTANT**: Never commit your `credentials.json` or `token.json` files to public repositories
- These files contain sensitive authentication information
- The `.gitignore` file is configured to exclude these files
- If you're forking this repository, make sure to set up your own credentials

## License

[MIT License](LICENSE)
