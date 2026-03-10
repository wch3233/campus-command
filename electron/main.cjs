const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");

let pythonProcess = null;
let mainWindow = null;

// ── Spawn Flask server ─────────────────────────────────────────────────────

function startPythonServer() {
  const serverPath = path.join(__dirname, "../server.py");
  const projectDir = path.join(__dirname, "..");

  // Load .env file so API key is available to Python
  const fs = require("fs");
  const envPath = path.join(projectDir, ".env");
  const envVars = { ...process.env };
  if (fs.existsSync(envPath)) {
    fs.readFileSync(envPath, "utf-8").split("\n").forEach((line) => {
      const match = line.match(/^([^#][^=]*)=(.*)$/);
      if (match) envVars[match[1].trim()] = match[2].trim();
    });
  }

  // Use full path to python3 in case PATH is limited in Electron context
  const python = envVars.PYTHON_PATH || "/opt/homebrew/bin/python3";

  pythonProcess = spawn(python, [serverPath], {
    cwd: projectDir,
    env: envVars,
    stdio: ["ignore", "pipe", "pipe"],
  });

  pythonProcess.stdout.on("data", (data) => {
    console.log("[Python]", data.toString().trim());
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error("[Python stderr]", data.toString().trim());
  });

  pythonProcess.on("exit", (code) => {
    console.log(`[Python] exited with code ${code}`);
  });
}

// ── Poll health endpoint ───────────────────────────────────────────────────

function waitForServer(retries, delay, callback) {
  if (retries <= 0) {
    callback(new Error("Flask server did not start in time."));
    return;
  }

  const req = http.get("http://127.0.0.1:5001/api/health", (res) => {
    if (res.statusCode === 200) {
      callback(null);
    } else {
      setTimeout(() => waitForServer(retries - 1, delay, callback), delay);
    }
  });

  req.on("error", () => {
    setTimeout(() => waitForServer(retries - 1, delay, callback), delay);
  });

  req.setTimeout(400, () => {
    req.destroy();
    setTimeout(() => waitForServer(retries - 1, delay, callback), delay);
  });
}

// ── Create BrowserWindow ───────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "default",
    backgroundColor: "#0F1929",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── App lifecycle ──────────────────────────────────────────────────────────

app.whenReady().then(() => {
  startPythonServer();

  // Poll up to 30 times at 500ms intervals = 15 seconds max
  waitForServer(30, 500, (err) => {
    if (err) {
      console.error("Could not reach Flask server:", err.message);
      // Still open the window — user will see connection error in UI
    }
    createWindow();
  });
});

app.on("window-all-closed", () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
});
