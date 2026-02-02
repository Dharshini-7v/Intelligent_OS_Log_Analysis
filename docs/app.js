// Simulated data and functionality for the frontend-only version
let currentUser = null;
let logStreamPaused = false;
let logEntries = [];
let patterns = [];
let anomalies = [];
let predictions = [];

// Demo users
const demoUsers = {
    'admin': { password: 'admin123', name: 'System Administrator', role: 'administrator' },
    'analyst': { password: 'analyst123', name: 'Log Analyst', role: 'log_analyst' },
    'demo': { password: 'demo', name: 'Demo User', role: 'viewer' }
};

// Login functionality
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.toLowerCase();
    const password = document.getElementById('password').value;
    
    if (demoUsers[username] && demoUsers[username].password === password) {
        currentUser = { username, ...demoUsers[username] };
        
        // Hide login overlay and show main app
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
        
        // Update user info in header
        document.getElementById('user-info').textContent = `${currentUser.name} (${currentUser.role})`;
        
        // Show admin nav if admin
        if (currentUser.role === 'administrator') {
            document.getElementById('admin-nav').style.display = 'flex';
            document.getElementById('admin-mobile-option').style.display = 'block';
        }
        
        // Initialize the dashboard
        initializeDashboard();
    } else {
        alert('Invalid username or password!');
    }
}

// Logout functionality
function logout() {
    currentUser = null;
    document.getElementById('login-overlay').style.display = 'flex';
    document.getElementById('main-app').style.display = 'none';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

// Initialize dashboard with simulated data
function initializeDashboard() {
    updateTime();
    setInterval(updateTime, 1000);
    
    initializeNavigation();
    generateSimulatedData();
    loadRecentActivity();
    
    // Start simulated real-time updates
    setInterval(updateSimulatedData, 3000);
}

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString();
}

// Navigation functionality
function initializeNavigation() {
    // Desktop navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            switchSection(section);
            
            // Update active nav item
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Mobile navigation
    document.getElementById('mobile-nav-select').addEventListener('change', function() {
        const section = this.value;
        switchSection(section);
    });
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Load section-specific data
    loadSectionData(sectionName);
}

function loadSectionData(section) {
    switch(section) {
        case 'dashboard':
            loadRecentActivity();
            break;
        case 'logs':
            updateLogStream();
            break;
        case 'patterns':
            updatePatterns();
            break;
        case 'anomalies':
            updateAnomalies();
            break;
        case 'predictions':
            updatePredictions();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'admin':
            if (currentUser.role === 'administrator') {
                loadUsers();
            }
            break;
    }
}

// Generate simulated data
function generateSimulatedData() {
    // Generate log entries
    const logLevels = ['INFO', 'WARNING', 'ERROR', 'DEBUG'];
    const sources = ['/var/log/auth.log', '/var/log/syslog', '/var/log/apache2/access.log', '/var/log/mysql/error.log'];
    const messages = [
        'User login successful for user{id}',
        'Failed authentication attempt from {ip}',
        'Database connection established',
        'High memory usage detected: {percent}%',
        'Service {service} started successfully',
        'Network timeout connecting to {host}',
        'Backup completed successfully',
        'Disk space warning: {percent}% full'
    ];
    
    for (let i = 0; i < 20; i++) {
        logEntries.push({
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            level: logLevels[Math.floor(Math.random() * logLevels.length)],
            source: sources[Math.floor(Math.random() * sources.length)],
            message: messages[Math.floor(Math.random() * messages.length)]
                .replace('{id}', Math.floor(Math.random() * 999) + 100)
                .replace('{ip}', `192.168.1.${Math.floor(Math.random() * 254) + 1}`)
                .replace('{percent}', Math.floor(Math.random() * 25) + 70)
                .replace('{service}', ['nginx', 'mysql', 'redis'][Math.floor(Math.random() * 3)])
                .replace('{host}', `server${Math.floor(Math.random() * 5) + 1}.example.com`)
        });
    }
    
    // Generate patterns
    const patternSequences = [
        ['login_attempt', 'authentication_success', 'session_start'],
        ['database_connect', 'query_execute', 'connection_close'],
        ['http_request', 'process_request', 'send_response'],
        ['backup_start', 'data_copy', 'backup_complete'],
        ['service_stop', 'cleanup', 'service_start']
    ];
    
    patternSequences.forEach((sequence, index) => {
        patterns.push({
            id: `pattern_${index + 1}`,
            sequence: sequence,
            frequency: Math.floor(Math.random() * 90) + 10,
            confidence: Math.random() * 0.3 + 0.7,
            pattern_type: ['normal', 'frequent', 'periodic'][Math.floor(Math.random() * 3)],
            last_seen: new Date(Date.now() - Math.random() * 3600000).toISOString()
        });
    });
    
    // Generate anomalies
    const anomalyTypes = [
        { title: 'High Error Rate', description: 'Unusual spike in error logs detected', severity: 'high' },
        { title: 'Suspicious Login Pattern', description: 'Multiple failed login attempts from same IP', severity: 'critical' },
        { title: 'Performance Degradation', description: 'Response times significantly increased', severity: 'medium' },
        { title: 'Unusual Network Activity', description: 'Abnormal network traffic patterns detected', severity: 'high' },
        { title: 'Resource Exhaustion', description: 'System resources approaching critical levels', severity: 'critical' }
    ];
    
    anomalyTypes.forEach((anomaly, index) => {
        if (Math.random() > 0.3) { // Only show some anomalies
            anomalies.push({
                id: `anomaly_${index + 1}`,
                ...anomaly,
                timestamp: new Date(Date.now() - Math.random() * 7200000).toISOString(),
                affected_sources: [sources[Math.floor(Math.random() * sources.length)]]
            });
        }
    });
    
    // Generate predictions
    const predictionTypes = [
        { type: 'system_failure', description: 'Potential disk space exhaustion in 4 hours', probability: 0.85, time_horizon: '4 hours' },
        { type: 'performance_degradation', description: 'Database performance may degrade due to high load', probability: 0.72, time_horizon: '2 hours' },
        { type: 'security_incident', description: 'Possible brute force attack based on login patterns', probability: 0.91, time_horizon: '30 minutes' }
    ];
    
    predictionTypes.forEach((pred, index) => {
        predictions.push({
            id: `prediction_${index + 1}`,
            ...pred,
            timestamp: new Date().toISOString()
        });
    });
}

// Update simulated data periodically
function updateSimulatedData() {
    // Add new log entry occasionally
    if (Math.random() > 0.7) {
        const newLog = {
            timestamp: new Date().toISOString(),
            level: ['INFO', 'WARNING', 'ERROR'][Math.floor(Math.random() * 3)],
            source: '/var/log/syslog',
            message: `System event ${Math.floor(Math.random() * 1000)} processed successfully`
        };
        logEntries.unshift(newLog);
        
        // Update counters
        document.getElementById('logs-processed').textContent = parseInt(document.getElementById('logs-processed').textContent) + 1;
        
        // Update log stream if visible and not paused
        if (!logStreamPaused && document.getElementById('logs-section').classList.contains('active')) {
            updateLogStream();
        }
    }
}

// Update log stream display
function updateLogStream() {
    const logStream = document.getElementById('log-stream');
    const recentLogs = logEntries.slice(0, 10);
    
    logStream.innerHTML = recentLogs.map(log => {
        const levelColor = {
            'ERROR': 'text-red-600 bg-red-50',
            'WARNING': 'text-yellow-600 bg-yellow-50',
            'INFO': 'text-blue-600 bg-blue-50',
            'DEBUG': 'text-gray-600 bg-gray-50'
        }[log.level] || 'text-gray-600 bg-gray-50';
        
        return `
            <div class="log-entry p-3 ${levelColor} rounded border-l-4 border-gray-300">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-1">
                            <span class="text-xs text-gray-500">${new Date(log.timestamp).toLocaleTimeString()}</span>
                            <span class="px-2 py-1 text-xs rounded ${levelColor}">${log.level}</span>
                            <span class="text-xs text-gray-400">${log.source}</span>
                        </div>
                        <p class="text-sm text-gray-800">${log.message}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Update patterns display
function updatePatterns() {
    const patternsList = document.getElementById('patterns-list');
    
    patternsList.innerHTML = patterns.slice(0, 5).map(pattern => `
        <div class="p-2 bg-gray-50 rounded border">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium">${pattern.sequence.join(' → ')}</p>
                    <p class="text-xs text-gray-500">Frequency: ${pattern.frequency}</p>
                </div>
                <span class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                    ${Math.round(pattern.confidence * 100)}%
                </span>
            </div>
        </div>
    `).join('');
    
    // Update pattern chart
    updatePatternChart();
}

// Update pattern chart
function updatePatternChart() {
    const ctx = document.getElementById('pattern-chart');
    if (!ctx) return;
    
    const normalCount = patterns.filter(p => p.pattern_type === 'normal').length;
    const frequentCount = patterns.filter(p => p.pattern_type === 'frequent').length;
    const periodicCount = patterns.filter(p => p.pattern_type === 'periodic').length;
    
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Normal Patterns', 'Frequent Patterns', 'Periodic Patterns'],
            datasets: [{
                data: [normalCount, frequentCount, periodicCount],
                backgroundColor: ['#10b981', '#3b82f6', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update anomalies display
function updateAnomalies() {
    const anomaliesList = document.getElementById('anomalies-list');
    
    if (anomalies.length === 0) {
        anomaliesList.innerHTML = '<p class="text-gray-500 text-sm">No recent anomalies</p>';
        return;
    }
    
    anomaliesList.innerHTML = anomalies.map(anomaly => {
        const severityColor = {
            'critical': 'border-red-500 bg-red-50',
            'high': 'border-orange-500 bg-orange-50',
            'medium': 'border-yellow-500 bg-yellow-50',
            'low': 'border-green-500 bg-green-50'
        }[anomaly.severity];
        
        return `
            <div class="p-3 ${severityColor} border-l-4 rounded">
                <div class="flex items-start justify-between">
                    <div>
                        <h4 class="font-medium text-gray-900 text-sm">${anomaly.title}</h4>
                        <p class="text-xs text-gray-600 mt-1">${anomaly.description}</p>
                        <p class="text-xs text-gray-400 mt-1">${new Date(anomaly.timestamp).toLocaleString()}</p>
                    </div>
                    <span class="px-2 py-1 text-xs rounded bg-red-100 text-red-800">${anomaly.severity}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Update predictions display
function updatePredictions() {
    const predictionsList = document.getElementById('predictions-list');
    
    if (predictions.length === 0) {
        predictionsList.innerHTML = '<p class="text-gray-500 text-sm">No recent predictions</p>';
        return;
    }
    
    predictionsList.innerHTML = predictions.map(prediction => {
        const probabilityColor = prediction.probability > 0.8 ? 'text-red-600' : 
                               prediction.probability > 0.6 ? 'text-yellow-600' : 'text-green-600';
        
        return `
            <div class="p-3 bg-purple-50 border-l-4 border-purple-400 rounded">
                <div>
                    <h4 class="font-medium text-gray-900 text-sm">${prediction.description}</h4>
                    <div class="flex items-center justify-between mt-2">
                        <span class="text-xs text-gray-500">In ${prediction.time_horizon}</span>
                        <span class="text-xs px-2 py-1 rounded bg-purple-100 ${probabilityColor}">
                            ${Math.round(prediction.probability * 100)}% confidence
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Load recent activity
function loadRecentActivity() {
    const activities = [
        { time: '2 min ago', type: 'anomaly', message: 'High error rate detected in auth service' },
        { time: '5 min ago', type: 'pattern', message: 'New pattern identified: login-success-logout' },
        { time: '8 min ago', type: 'prediction', message: 'Predicted disk space exhaustion in 4 hours' },
        { time: '12 min ago', type: 'log', message: '1,247 new log entries processed' },
        { time: '15 min ago', type: 'user', message: 'New user registered: analyst_john' }
    ];
    
    const activityHtml = activities.map(activity => {
        const iconClass = {
            'anomaly': 'fas fa-exclamation-triangle text-red-500',
            'pattern': 'fas fa-search text-purple-500',
            'prediction': 'fas fa-crystal-ball text-indigo-500',
            'log': 'fas fa-file-alt text-blue-500',
            'user': 'fas fa-user text-green-500'
        }[activity.type];
        
        return `
            <div class="flex items-start space-x-3 p-3 bg-gray-50 rounded">
                <i class="${iconClass}"></i>
                <div class="flex-1">
                    <p class="text-sm text-gray-800">${activity.message}</p>
                    <p class="text-xs text-gray-500">${activity.time}</p>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('recent-activity').innerHTML = activityHtml;
}

// Load analytics
function loadAnalytics() {
    loadPerformanceChart();
    loadSystemHealth();
}

function loadPerformanceChart() {
    const ctx = document.getElementById('performance-chart');
    if (!ctx) return;
    
    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
            datasets: [{
                label: 'CPU Usage (%)',
                data: [45, 52, 48, 61, 55],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4
            }, {
                label: 'Memory Usage (%)',
                data: [38, 42, 45, 48, 46],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function loadSystemHealth() {
    const healthMetrics = [
        { name: 'Database Connection', status: 'healthy', value: '99.9% uptime' },
        { name: 'Log Processing', status: 'healthy', value: '1,247 logs/min' },
        { name: 'Pattern Detection', status: 'warning', value: '12 patterns/hour' },
        { name: 'Anomaly Detection', status: 'healthy', value: '3 anomalies detected' },
        { name: 'Prediction Engine', status: 'healthy', value: '95% accuracy' }
    ];
    
    const healthHtml = healthMetrics.map(metric => {
        const statusClass = {
            'healthy': 'text-green-600 bg-green-100',
            'warning': 'text-yellow-600 bg-yellow-100',
            'error': 'text-red-600 bg-red-100'
        }[metric.status];
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                    <p class="text-sm font-medium text-gray-800">${metric.name}</p>
                    <p class="text-xs text-gray-500">${metric.value}</p>
                </div>
                <span class="px-2 py-1 text-xs rounded ${statusClass}">${metric.status}</span>
            </div>
        `;
    }).join('');
    
    document.getElementById('system-health').innerHTML = healthHtml;
}

// Load users (admin only)
function loadUsers() {
    if (currentUser.role !== 'administrator') {
        document.getElementById('users-table').innerHTML = '<p class="text-red-500">Access denied. Admin privileges required.</p>';
        return;
    }
    
    const users = [
        { username: 'admin', name: 'System Administrator', email: 'admin@loganalysis.com', role: 'administrator', created_at: '2024-01-15', is_demo_account: true },
        { username: 'analyst', name: 'Log Analyst', email: 'analyst@loganalysis.com', role: 'log_analyst', created_at: '2024-01-16', is_demo_account: true },
        { username: 'demo', name: 'Demo User', email: 'demo@loganalysis.com', role: 'viewer', created_at: '2024-01-17', is_demo_account: true },
        { username: 'john_doe', name: 'John Doe', email: 'john@company.com', role: 'log_analyst', created_at: '2024-02-01', is_demo_account: false },
        { username: 'jane_smith', name: 'Jane Smith', email: 'jane@company.com', role: 'viewer', created_at: '2024-02-02', is_demo_account: false }
    ];
    
    let tableHTML = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
    `;

    users.forEach(user => {
        const roleColor = {
            'administrator': 'bg-red-100 text-red-800',
            'log_analyst': 'bg-blue-100 text-blue-800',
            'viewer': 'bg-green-100 text-green-800'
        }[user.role] || 'bg-gray-100 text-gray-800';

        const accountType = user.is_demo_account ? 
            '<span class="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Demo</span>' :
            '<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">Registered</span>';

        tableHTML += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${user.username}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.email}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs rounded ${roleColor}">${user.role.replace('_', ' ')}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.created_at}</td>
                <td class="px-6 py-4 whitespace-nowrap">${accountType}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    document.getElementById('users-table').innerHTML = tableHTML;
}

// Quick actions
function refreshData() {
    generateSimulatedData();
    loadSectionData('dashboard');
    showNotification('Data Refreshed', 'All data has been updated', 'success');
}

function exportLogs() {
    showNotification('Export Started', 'Log export is being prepared', 'info');
    setTimeout(() => {
        showNotification('Export Complete', 'Logs have been exported successfully', 'success');
    }, 2000);
}

function clearAlerts() {
    anomalies = [];
    document.getElementById('anomalies-list').innerHTML = '<p class="text-gray-500 text-sm">No active alerts</p>';
    document.getElementById('anomalies-found').textContent = '0';
    showNotification('Alerts Cleared', 'All alerts have been cleared', 'success');
}

// Log stream controls
function pauseLogStream() {
    const btn = document.getElementById('pause-logs-btn');
    if (logStreamPaused) {
        logStreamPaused = false;
        btn.innerHTML = '<i class="fas fa-pause mr-1"></i>Pause';
        btn.className = 'px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700';
    } else {
        logStreamPaused = true;
        btn.innerHTML = '<i class="fas fa-play mr-1"></i>Resume';
        btn.className = 'px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700';
    }
}

// Notification system
function showNotification(title, message, type) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'error' ? 'bg-red-500' : 
        type === 'warning' ? 'bg-yellow-500' : 
        type === 'success' ? 'bg-green-500' : 'bg-blue-500'
    } text-white`;
    
    notification.innerHTML = `
        <h4 class="font-bold">${title}</h4>
        <p class="text-sm">${message}</p>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}