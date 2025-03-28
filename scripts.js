// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatDuration(duration) {
    // Parse ISO 8601 duration format (e.g., PT22M57S)
    const matches = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!matches) return '';
    
    const hours = matches[1] ? parseInt(matches[1]) : 0;
    const minutes = matches[2] ? parseInt(matches[2]) : 0;
    const seconds = matches[3] ? parseInt(matches[3]) : 0;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Main function to load and display data
async function loadMediaKitData() {
    try {
        const response = await fetch('youtube_media_kit.json');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display data once loaded
        displayChannelInfo(data);
        displayAudienceDemographics(data);
        displayPerformanceMetrics(data);
        
    } catch (error) {
        console.error('Error loading media kit data:', error);
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.innerHTML = `<p style="color: red;">Error loading data: ${error.message}</p>`;
        });
    }
}

// Display channel information
function displayChannelInfo(data) {
    const channelInfo = data.channelInfo;
    
    // Set channel thumbnail
    document.getElementById('channel-thumbnail').src = channelInfo.thumbnails.high.url;
    
    // Set channel title and custom URL
    document.getElementById('channel-title').textContent = channelInfo.title;
    document.getElementById('channel-custom-url').textContent = channelInfo.customUrl;
    
    // Set key metrics
    document.getElementById('subscriber-count').textContent = formatNumber(channelInfo.subscriberCount);
    document.getElementById('view-count').textContent = formatNumber(channelInfo.viewCount);
    document.getElementById('video-count').textContent = formatNumber(channelInfo.videoCount);
    
    // Show content and hide loader
    document.getElementById('header-loader').style.display = 'none';
    document.querySelector('.header-content').style.display = 'block';
}

// Display audience demographics
function displayAudienceDemographics(data) {
    const audience = data.audience;
    
    // Create age and gender chart
    createAgeGenderChart(audience.ageGender);
    
    // Create countries chart
    createCountriesChart(audience.countries);
    
    // Create devices chart
    createDevicesChart(audience.devices);
    
    // Show content and hide loader
    document.getElementById('demographics-loader').style.display = 'none';
    document.querySelector('.demographics-content').style.display = 'block';
}

// Create age and gender chart
function createAgeGenderChart(ageGenderData) {
    const ctx = document.getElementById('ageGenderChart').getContext('2d');
    
    // Prepare data
    const ageGroups = ['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'];
    const maleData = [];
    const femaleData = [];
    
    ageGroups.forEach(group => {
        const ageKey = `age${group}`;
        maleData.push(ageGenderData.male[ageKey] || 0);
        femaleData.push(ageGenderData.female[ageKey] || 0);
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ageGroups,
            datasets: [
                {
                    label: 'Male',
                    data: maleData,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Female',
                    data: femaleData,
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: false,
                    title: {
                        display: true,
                        text: 'Age Group'
                    }
                },
                y: {
                    stacked: false,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Audience by Age and Gender'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

// Create countries chart
function createCountriesChart(countriesData) {
    const ctx = document.getElementById('countriesChart').getContext('2d');
    
    // Get top 10 countries
    const countries = Object.entries(countriesData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    const labels = countries.map(country => country[0]);
    const data = countries.map(country => country[1]);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Audience Percentage',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Countries'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toFixed(2)}%`;
                        }
                    }
                }
            }
        }
    });
}

// Create devices chart
function createDevicesChart(devicesData) {
    const ctx = document.getElementById('devicesChart').getContext('2d');
    
    const labels = Object.keys(devicesData);
    const data = labels.map(device => devicesData[device].percentage);
    
    // Custom colors for devices
    const backgroundColors = [
        'rgba(54, 162, 235, 0.7)', // Mobile
        'rgba(75, 192, 192, 0.7)',  // Desktop
        'rgba(153, 102, 255, 0.7)', // TV
        'rgba(255, 159, 64, 0.7)'   // Tablet
    ];
    
    const borderColors = [
        'rgba(54, 162, 235, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Device Distribution'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const device = labels[context.dataIndex];
                            const views = formatNumber(devicesData[device].views);
                            const percentage = devicesData[device].percentage.toFixed(1);
                            return `${device}: ${percentage}% (${views} views)`;
                        }
                    }
                }
            }
        }
    });
}

// Display performance metrics
function displayPerformanceMetrics(data) {
    const performance = data.performance;
    
    // Average metrics
    document.getElementById('avg-view-percentage').textContent = performance.averages.averageViewPercentage + '%';
    document.getElementById('avg-daily-views').textContent = formatNumber(performance.averages.dailyViews);
    document.getElementById('avg-views-per-video').textContent = formatNumber(performance.averages.viewsPerVideo);
    
    // Show content and hide loader
    document.getElementById('performance-loader').style.display = 'none';
    document.querySelector('.performance-content').style.display = 'block';
}

// Display top content
function displayTopContent(data) {
    const topVideos = data.topContent.topVideos;
    const videosContainer = document.getElementById('videos-container');
    
    topVideos.forEach(video => {
        const videoCard = document.createElement('div');
        videoCard.className = 'video-card';
        
        const videoUrl = `https://www.youtube.com/watch?v=${video.id}`;
        
        videoCard.innerHTML = `
            <a href="${videoUrl}" target="_blank" rel="noopener noreferrer">
                <img src="${video.thumbnails.maxres ? video.thumbnails.maxres.url : video.thumbnails.high.url}" alt="${video.title}" class="video-thumbnail">
            </a>
            <div class="video-info">
                <a href="${videoUrl}" target="_blank" rel="noopener noreferrer" class="video-title-link">
                    <h3 class="video-title">${video.title}</h3>
                </a>
                <div class="video-date">${formatDate(video.publishedAt)} • ${formatDuration(video.duration)}</div>
                <div class="video-stats">
                    <div class="video-stat">
                        <i class="fas fa-eye"></i>
                        <span class="video-stat-value">${formatNumber(video.viewCount)}</span>
                        <span class="video-stat-label">Views</span>
                    </div>
                    <div class="video-stat">
                        <i class="fas fa-thumbs-up"></i>
                        <span class="video-stat-value">${formatNumber(video.likeCount)}</span>
                        <span class="video-stat-label">Likes</span>
                    </div>
                    <div class="video-stat">
                        <i class="fas fa-comment"></i>
                        <span class="video-stat-value">${formatNumber(video.commentCount)}</span>
                        <span class="video-stat-label">Comments</span>
                    </div>
                </div>
            </div>
        `;
        
        videosContainer.appendChild(videoCard);
    });
    
    // Show content and hide loader
    document.getElementById('content-loader').style.display = 'none';
    document.querySelector('.top-content-container').style.display = 'block';
}

// Update sponsorship section
function updateSponsorshipSection(data) {
    document.getElementById('subscriber-count-cta').textContent = formatNumber(data.channelInfo.subscriberCount);
    document.getElementById('engagement-rate-cta').textContent = data.performance.averages.engagementRate + '%';
}

// Load data when the page is ready
document.addEventListener('DOMContentLoaded', loadMediaKitData);
