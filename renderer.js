// Global variables to store data
let matchedGames = null;

// Helper function to set busy state
function setBusyState(isBusy) {
    const elements = [
        document.getElementById('steamProfile'),
        document.getElementById('apiKey'),
        document.getElementById('updateDatabase'),
        document.getElementById('checkCompatibility')
    ];

    elements.forEach(element => {
        element.disabled = isBusy;
    });

    // Don't disable save button here, it's controlled separately
}

// Helper function to update progress bar
function updateProgress(isActive, progress = 0) {
    const progressBar = document.getElementById('progressBarInner');

    if (isActive) {
        if (progress > 0) {
            // Determinate progress
            progressBar.style.width = `${progress}%`;
        } else {
            // Indeterminate progress - animate
            progressBar.style.width = '100%';
            progressBar.style.animation = 'progress-indeterminate 1.5s infinite linear';
            progressBar.style.backgroundImage = 'linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent)';
            progressBar.style.backgroundSize = '40px 40px';
        }
    } else {
        // Reset progress bar
        progressBar.style.width = '0%';
        progressBar.style.animation = 'none';
        progressBar.style.backgroundImage = 'none';
    }
}

// Helper function to update status text
function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

// Helper function to check if database exists and show last update time
async function checkDatabaseStatus() {
    try {
        const response = await window.api.fetch('http://localhost:5000/database-status', { method: 'GET' });
        if (response.exists) {
            updateStatus(`Database last updated: ${response.last_updated}`);
        } else {
            updateStatus('Database not found. Please update the database.');
        }
    } catch (error) {
        console.error('Error checking database status:', error);
        updateStatus('Error checking database status');
    }
}

// Helper function to display results
function displayResults(username, games) {
    const resultsTextarea = document.getElementById('results');

    // Get selected comparison options
    const showNative = document.getElementById('compareNative').checked;
    const showRosetta = document.getElementById('compareRosetta').checked;
    const showCrossover = document.getElementById('compareCrossover').checked;
    const showWine = document.getElementById('compareWine').checked;
    const showParallels = document.getElementById('compareParallels').checked;
    const showLinuxArm = document.getElementById('compareLinuxArm').checked;

    // Build header based on selected options
    let header = `Compatibility information for ${username}'s Steam games:\n`;
    header += '-'.repeat(80) + '\n';

    let columnHeader = 'Game Name'.padEnd(40);
    if (showNative) columnHeader += 'Native'.padEnd(10);
    if (showRosetta) columnHeader += 'Rosetta 2'.padEnd(10);
    if (showCrossover) columnHeader += 'CrossOver'.padEnd(10);
    if (showWine) columnHeader += 'Wine'.padEnd(10);
    if (showParallels) columnHeader += 'Parallels'.padEnd(10);
    if (showLinuxArm) columnHeader += 'Linux ARM'.padEnd(10);

    header += columnHeader + '\n';
    header += '-'.repeat(80) + '\n';

    // Build rows for each game
    let rows = '';
    for (const game of games) {
        let row = game.name.substring(0, 39).padEnd(40);

        if (showNative) row += (game.native || 'Unknown').padEnd(10);
        if (showRosetta) row += (game.rosetta_2 || 'Unknown').padEnd(10);
        if (showCrossover) row += (game.crossover || 'Unknown').padEnd(10);
        if (showWine) row += (game.wine || 'Unknown').padEnd(10);
        if (showParallels) row += (game.parallels || 'Unknown').padEnd(10);
        if (showLinuxArm) row += (game.linux_arm || 'Unknown').padEnd(10);

        rows += row + '\n';
    }

    resultsTextarea.value = header + rows;
}

// Update Database button click handler
document.getElementById('updateDatabase').addEventListener('click', async () => {
    console.log('Update Database button clicked.');

    setBusyState(true);
    updateStatus('Updating database...');
    updateProgress(true);

    try {
        const response = await window.api.fetch('http://localhost:5000/update-database', { 
            method: 'POST' 
        });

        console.log('Server response:', response);

        if (response.message) {
            updateStatus(`Database updated with ${response.game_count} games.`);
        } else if (response.error) {
            updateStatus(`Error: ${response.error}`);
        }
    } catch (error) {
        console.error('Error updating the database:', error);
        updateStatus(`Error updating database: ${error.message}`);
    } finally {
        setBusyState(false);
        updateProgress(false);
        await checkDatabaseStatus();
    }
});

// Check Compatibility button click handler
document.getElementById('checkCompatibility').addEventListener('click', async () => {
    console.log('Check Compatibility button clicked.');

    const steamProfile = document.getElementById('steamProfile').value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();

    if (!steamProfile) {
        alert('Please enter a Steam profile URL.');
        return;
    }

    setBusyState(true);
    updateStatus('Checking compatibility...');
    updateProgress(true);

    try {
        const response = await window.api.fetch('http://localhost:5000/check-compatibility', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                steam_profile: steamProfile,
                api_key: apiKey
            })
        });

        console.log('Server response:', response);

        if (response.matched_games) {
            matchedGames = response.matched_games;
            displayResults(response.username, matchedGames);
            updateStatus(`Found ${response.game_count} games for ${response.username}. Matched with compatibility data.`);
            document.getElementById('saveResults').disabled = false;
        } else if (response.error) {
            updateStatus(`Error: ${response.error}`);
        }
    } catch (error) {
        console.error('Error checking compatibility:', error);
        updateStatus(`Error checking compatibility: ${error.message}`);
    } finally {
        setBusyState(false);
        updateProgress(false);
    }
});

// Save Results button click handler
document.getElementById('saveResults').addEventListener('click', async () => {
    console.log('Save Results button clicked.');

    if (!matchedGames) {
        alert('No compatibility data to save.');
        return;
    }

    try {
        const savePath = await window.api.showSaveDialog({
            title: 'Save Compatibility Results',
            defaultPath: 'compatibility_results.csv',
            filters: [
                { name: 'CSV Files', extensions: ['csv'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });

        if (!savePath) {
            return; // User cancelled
        }

        const response = await window.api.fetch('http://localhost:5000/save-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                matched_games: matchedGames,
                file_path: savePath
            })
        });

        console.log('Server response:', response);

        if (response.message) {
            alert(response.message);
        } else if (response.error) {
            alert(`Error: ${response.error}`);
        }
    } catch (error) {
        console.error('Error saving results:', error);
        alert(`Error saving results: ${error.message}`);
    }
});

// Add event listeners for comparison checkboxes to update display when changed
document.querySelectorAll('.checkbox-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
        if (matchedGames) {
            // Re-display results with updated comparison options
            const response = window.api.getUsername();
            if (response && response.username) {
                displayResults(response.username, matchedGames);
            } else {
                displayResults('Unknown', matchedGames);
            }
        }
    });
});

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await checkDatabaseStatus();
});
