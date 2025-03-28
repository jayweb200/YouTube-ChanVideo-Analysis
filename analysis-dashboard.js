// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function getEngagementClass(rate) {
    if (rate >= 3.5) return 'high';
    if (rate >= 2.0) return 'medium';
    return 'low';
}

function getRetentionClass(rate) {
    if (rate >= 30) return 'high';
    if (rate >= 20) return 'medium';
    return 'low';
}

function sanitizeHTML(text) {
    const element = document.createElement('div');
    element.textContent = text;
    return element.innerHTML;
}

// Main function to load and display data
async function loadAnalysisData() {
    try {
        const response = await fetch('youtube_analysis_ui.json');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display data once loaded
        displayChannelInfo(data);
        displayTopVideos(data);
        displayVideoAnalysis(data);
        displayPatternsRecommendations(data);
        
        // Setup event listeners
        setupEventListeners();
        
    } catch (error) {
        console.error('Error loading analysis data:', error);
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.innerHTML = `<p style="color: red;">Error loading data: ${error.message}</p>`;
        });
    }
}

// Display channel information
function displayChannelInfo(data) {
    // Set channel name
    document.getElementById('channel-name').textContent = data.channel_name;
    
    // Set subscriber count
    document.getElementById('subscriber-count').textContent = formatNumber(parseInt(data.channel_subscribers));
    
    // Calculate total views from top videos
    const totalViews = data.top_videos.reduce((sum, video) => sum + video.views, 0);
    document.getElementById('total-views').textContent = formatNumber(totalViews);
    
    // Calculate average engagement rate
    let totalEngagement = 0;
    let videoCount = 0;
    
    for (const videoId in data.video_analyses) {
        const metrics = data.video_analyses[videoId].structured_analysis.metrics;
        if (metrics && metrics.engagement_rate) {
            const engagementRate = parseFloat(metrics.engagement_rate);
            if (!isNaN(engagementRate)) {
                totalEngagement += engagementRate;
                videoCount++;
            }
        }
    }
    
    const avgEngagement = videoCount > 0 ? (totalEngagement / videoCount).toFixed(1) + '%' : 'N/A';
    document.getElementById('avg-engagement').textContent = avgEngagement;
    
    // Show content and hide loader
    document.getElementById('header-loader').style.display = 'none';
    document.querySelector('.header-content').style.display = 'block';
}

// Display top videos
function displayTopVideos(data) {
    const tableBody = document.getElementById('videos-table-body');
    tableBody.innerHTML = '';
    
    data.top_videos.forEach((video, index) => {
        const videoId = video.video_id;
        const videoAnalysis = data.video_analyses[videoId];
        
        if (!videoAnalysis) return;
        
        const metrics = videoAnalysis.structured_analysis.metrics;
        const engagementRate = metrics.engagement_rate ? parseFloat(metrics.engagement_rate) : 0;
        const retentionRate = metrics.retention_rate ? parseFloat(metrics.retention_rate) : 0;
        
        const engagementClass = getEngagementClass(engagementRate);
        const retentionClass = getRetentionClass(retentionRate);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${video.rank}</td>
            <td>
                <img src="https://i.ytimg.com/vi/${videoId}/mqdefault.jpg" alt="${sanitizeHTML(video.title)}" class="video-thumbnail-small">
            </td>
            <td class="video-title-cell">
                <div class="video-title-text">${sanitizeHTML(video.title)}</div>
            </td>
            <td>${formatNumber(video.views)}</td>
            <td class="engagement-cell">
                <span class="engagement-badge ${engagementClass}">${metrics.engagement_rate || 'N/A'}</span>
            </td>
            <td class="retention-cell">
                <span class="retention-badge ${retentionClass}">${metrics.retention_rate || 'N/A'}</span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="action-button view-analysis" data-video-id="${videoId}">
                        <i class="fas fa-chart-bar"></i> Analysis
                    </button>
                    <a href="https://www.youtube.com/watch?v=${videoId}" target="_blank" class="action-button">
                        <i class="fas fa-external-link-alt"></i> Watch
                    </a>
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Show content and hide loader
    document.getElementById('videos-loader').style.display = 'none';
    document.querySelector('.videos-content').style.display = 'block';
}

// Display video analysis
function displayVideoAnalysis(data) {
    const tabButtons = document.getElementById('video-tabs');
    const tabContent = document.getElementById('video-tab-content');
    
    tabButtons.innerHTML = '';
    tabContent.innerHTML = '';
    
    // Create tabs for each video
    data.top_videos.forEach((video, index) => {
        const videoId = video.video_id;
        const videoAnalysis = data.video_analyses[videoId];
        
        if (!videoAnalysis) return;
        
        // Create tab button
        const tabButton = document.createElement('button');
        tabButton.className = `tab-button ${index === 0 ? 'active' : ''}`;
        tabButton.setAttribute('data-tab', `video-${videoId}`);
        tabButton.textContent = `${index + 1}. ${video.title.length > 25 ? video.title.substring(0, 25) + '...' : video.title}`;
        tabButtons.appendChild(tabButton);
        
        // Create tab content
        const tabPane = document.createElement('div');
        tabPane.className = `tab-pane ${index === 0 ? 'active' : ''}`;
        tabPane.id = `video-${videoId}`;
        
        const analysis = videoAnalysis.structured_analysis;
        const metrics = analysis.metrics;
        
        tabPane.innerHTML = `
            <div class="video-analysis-card">
                <div class="video-header">
                    <div class="video-thumbnail-container">
                        <img src="https://i.ytimg.com/vi/${videoId}/hqdefault.jpg" alt="${sanitizeHTML(video.title)}" class="video-thumbnail-large">
                    </div>
                    <div class="video-info-container">
                        <h2 class="video-title-large">${sanitizeHTML(video.title)}</h2>
                        <div class="video-metrics-grid">
                            <div class="video-metric-item">
                                <i class="fas fa-eye"></i>
                                <span class="video-metric-value">${formatNumber(video.views)}</span>
                                <span class="video-metric-label">Views</span>
                            </div>
                            <div class="video-metric-item">
                                <i class="fas fa-thumbs-up"></i>
                                <span class="video-metric-value">${metrics.likes ? formatNumber(parseInt(metrics.likes)) : 'N/A'}</span>
                                <span class="video-metric-label">Likes</span>
                            </div>
                            <div class="video-metric-item">
                                <i class="fas fa-comment"></i>
                                <span class="video-metric-value">${metrics.comments ? formatNumber(parseInt(metrics.comments)) : 'N/A'}</span>
                                <span class="video-metric-label">Comments</span>
                            </div>
                            <div class="video-metric-item">
                                <i class="fas fa-chart-line"></i>
                                <span class="video-metric-value">${metrics.engagement_rate || 'N/A'}</span>
                                <span class="video-metric-label">Engagement</span>
                            </div>
                            <div class="video-metric-item">
                                <i class="fas fa-clock"></i>
                                <span class="video-metric-value">${metrics.avg_view_duration || 'N/A'}</span>
                                <span class="video-metric-label">Avg Duration</span>
                            </div>
                            <div class="video-metric-item">
                                <i class="fas fa-percentage"></i>
                                <span class="video-metric-value">${metrics.retention_rate || 'N/A'}</span>
                                <span class="video-metric-label">Retention</span>
                            </div>
                        </div>
                        <a href="${analysis.video_url}" target="_blank" class="video-url">
                            <i class="fas fa-external-link-alt"></i> Watch on YouTube
                        </a>
                    </div>
                </div>
                
                <div class="analysis-section">
                    <h3>Title Analysis</h3>
                    <div class="analysis-content">
                        ${analysis.title_analysis.full_text}
                    </div>
                    ${renderTitleHighlights(analysis.title_analysis)}
                </div>
                
                <div class="analysis-section">
                    <h3>Thumbnail Analysis</h3>
                    <div class="analysis-content">
                        ${analysis.thumbnail_analysis.full_text}
                    </div>
                    ${renderThumbnailHighlights(analysis.thumbnail_analysis)}
                </div>
            </div>
        `;
        
        tabContent.appendChild(tabPane);
    });
    
    // Show content and hide loader
    document.getElementById('analysis-loader').style.display = 'none';
    document.querySelector('.analysis-content').style.display = 'block';
}

// Render title analysis highlights
function renderTitleHighlights(titleAnalysis) {
    if (!titleAnalysis.sections || Object.keys(titleAnalysis.sections).length === 0) {
        return '';
    }
    
    let html = '<div class="analysis-highlights">';
    
    for (const [key, content] of Object.entries(titleAnalysis.sections)) {
        const title = key.replace(/[*_]/g, '').trim();
        html += `
            <div class="highlight-item">
                <h4>${title.charAt(0).toUpperCase() + title.slice(1)}</h4>
                <p>${content}</p>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Render thumbnail analysis highlights
function renderThumbnailHighlights(thumbnailAnalysis) {
    if (!thumbnailAnalysis.sections || Object.keys(thumbnailAnalysis.sections).length === 0) {
        return '';
    }
    
    let html = '<div class="analysis-highlights">';
    
    for (const [key, content] of Object.entries(thumbnailAnalysis.sections)) {
        const title = key.replace(/[*_]/g, '').trim();
        html += `
            <div class="highlight-item">
                <h4>${title.charAt(0).toUpperCase() + title.slice(1)}</h4>
                <p>${content}</p>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Display patterns and recommendations
function displayPatternsRecommendations(data) {
    const patternsReport = data.patterns_report;
    
    // Process common patterns
    const patternsCommonContainer = document.getElementById('patterns-common');
    const commonPatterns = extractPatternsFromSection(patternsReport, 'common patterns and success factors');
    
    patternsCommonContainer.innerHTML = '';
    commonPatterns.forEach(pattern => {
        const patternItem = document.createElement('div');
        patternItem.className = 'pattern-item';
        patternItem.innerHTML = `
            <h4>${pattern.title}</h4>
            <p>${pattern.content}</p>
        `;
        patternsCommonContainer.appendChild(patternItem);
    });
    
    // Process success factors (using the same section for now, but could be separated in the future)
    const patternsSuccessContainer = document.getElementById('patterns-success');
    const successFactors = extractSuccessFactorsFromSection(patternsReport, 'common patterns and success factors');
    
    patternsSuccessContainer.innerHTML = '';
    successFactors.forEach(factor => {
        const factorItem = document.createElement('div');
        factorItem.className = 'pattern-item';
        factorItem.innerHTML = `
            <h4>${factor.title}</h4>
            <p>${factor.content}</p>
        `;
        patternsSuccessContainer.appendChild(factorItem);
    });
    
    // Process recommendations
    const recommendationsContainer = document.getElementById('recommendations');
    const recommendations = extractRecommendationsFromSection(patternsReport, 'actionable recommendations');
    
    recommendationsContainer.innerHTML = '';
    recommendations.forEach(recommendation => {
        const recommendationItem = document.createElement('div');
        recommendationItem.className = 'recommendation-item';
        recommendationItem.innerHTML = `
            <h4>${recommendation.title}</h4>
            <p>${recommendation.content}</p>
        `;
        recommendationsContainer.appendChild(recommendationItem);
    });
    
    // Show content and hide loader
    document.getElementById('patterns-loader').style.display = 'none';
    document.querySelector('.patterns-content').style.display = 'block';
}

// Extract patterns from section
function extractPatternsFromSection(patternsReport, sectionName) {
    if (!patternsReport.sections || !patternsReport.sections[sectionName]) {
        return [];
    }
    
    const sectionContent = patternsReport.sections[sectionName];
    const patterns = [];
    
    // Split by numbered items (1., 2., etc.)
    const patternRegex = /(\d+\.\s+\*\*[^:]+\*\*:?)/g;
    const patternParts = sectionContent.split(patternRegex);
    
    for (let i = 1; i < patternParts.length; i += 2) {
        const title = patternParts[i].replace(/\d+\.\s+\*\*/g, '').replace(/\*\*:?/g, '').trim();
        const content = patternParts[i + 1].trim();
        
        patterns.push({
            title,
            content
        });
    }
    
    return patterns;
}

// Extract success factors from section (focusing on the second half of patterns)
function extractSuccessFactorsFromSection(patternsReport, sectionName) {
    if (!patternsReport.sections || !patternsReport.sections[sectionName]) {
        return [];
    }
    
    const sectionContent = patternsReport.sections[sectionName];
    const factors = [];
    
    // Split by numbered items (1., 2., etc.)
    const factorRegex = /(\d+\.\s+\*\*[^:]+\*\*:?)/g;
    const factorParts = sectionContent.split(factorRegex);
    
    // Get the second half of the patterns (3 and 4 typically)
    const startIndex = Math.ceil(factorParts.length / 2);
    
    for (let i = startIndex; i < factorParts.length; i += 2) {
        if (i + 1 >= factorParts.length) continue;
        
        const title = factorParts[i].replace(/\d+\.\s+\*\*/g, '').replace(/\*\*:?/g, '').trim();
        const content = factorParts[i + 1].trim();
        
        factors.push({
            title,
            content
        });
    }
    
    return factors;
}

// Extract recommendations from section
function extractRecommendationsFromSection(patternsReport, sectionName) {
    if (!patternsReport.sections || !patternsReport.sections[sectionName]) {
        return [];
    }
    
    const sectionContent = patternsReport.sections[sectionName];
    const recommendations = [];
    
    // Split by numbered items (1., 2., etc.)
    const recommendationRegex = /(\d+\.\s+\*\*[^:]+\*\*:?)/g;
    const recommendationParts = sectionContent.split(recommendationRegex);
    
    for (let i = 1; i < recommendationParts.length; i += 2) {
        const title = recommendationParts[i].replace(/\d+\.\s+\*\*/g, '').replace(/\*\*:?/g, '').trim();
        const content = recommendationParts[i + 1].trim();
        
        recommendations.push({
            title,
            content
        });
    }
    
    return recommendations;
}

// Setup event listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Update active tab button
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            button.classList.add('active');
            
            // Update active tab content
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // View analysis buttons
    document.querySelectorAll('.view-analysis').forEach(button => {
        button.addEventListener('click', () => {
            const videoId = button.getAttribute('data-video-id');
            const tabButton = document.querySelector(`.tab-button[data-tab="video-${videoId}"]`);
            
            if (tabButton) {
                // Scroll to analysis section
                document.getElementById('video-analysis').scrollIntoView({ behavior: 'smooth' });
                
                // Trigger click on the tab button
                setTimeout(() => {
                    tabButton.click();
                }, 500);
            }
        });
    });
    
    // Search functionality
    document.getElementById('video-search').addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const tableRows = document.querySelectorAll('#videos-table-body tr');
        
        tableRows.forEach(row => {
            const title = row.querySelector('.video-title-text').textContent.toLowerCase();
            if (title.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
    
    // Sort functionality
    document.getElementById('sort-by').addEventListener('change', (e) => {
        const sortValue = e.target.value;
        const tableBody = document.getElementById('videos-table-body');
        const tableRows = Array.from(tableBody.querySelectorAll('tr'));
        
        tableRows.sort((a, b) => {
            let valueA, valueB;
            
            if (sortValue.startsWith('views')) {
                valueA = parseInt(a.querySelector('td:nth-child(4)').textContent.replace(/[^\d]/g, ''));
                valueB = parseInt(b.querySelector('td:nth-child(4)').textContent.replace(/[^\d]/g, ''));
            } else if (sortValue.startsWith('engagement')) {
                valueA = parseFloat(a.querySelector('.engagement-badge').textContent) || 0;
                valueB = parseFloat(b.querySelector('.engagement-badge').textContent) || 0;
            }
            
            return sortValue.endsWith('asc') ? valueA - valueB : valueB - valueA;
        });
        
        // Clear table and append sorted rows
        tableBody.innerHTML = '';
        tableRows.forEach(row => {
            tableBody.appendChild(row);
        });
    });
}

// Load data when the page is ready
document.addEventListener('DOMContentLoaded', loadAnalysisData);
