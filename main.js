const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

// Start the Flask backend server
function startBackend() {
    // Check if Python is available
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

    // Start the backend process
    backendProcess = spawn(pythonCommand, [path.join(__dirname, 'backend.py')]);

    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });
}

// Create the main window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 900,
        height: 700,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    mainWindow.loadFile('index.html');

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

// Handle the save dialog IPC call
ipcMain.handle('show-save-dialog', async (event, options) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, options);
    if (canceled) {
        return null;
    }
    return filePath;
});

// App lifecycle events
app.on('ready', () => {
    startBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('will-quit', () => {
    // Kill the backend process when the app is closing
    if (backendProcess) {
        if (process.platform === 'win32') {
            // On Windows, we need to kill the process tree
            spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
        } else {
            // On Unix-like systems, we can just kill the process
            backendProcess.kill();
        }
    }
});
