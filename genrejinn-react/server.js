const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Ensure data directory exists
const dataDir = path.join(__dirname, 'data');
fs.mkdir(dataDir, { recursive: true }).catch(() => {});

// Save reading progress
app.post('/api/save-progress', async (req, res) => {
  try {
    const { location, timestamp = Date.now() } = req.body;

    const progressData = {
      location,
      timestamp,
      savedAt: new Date().toISOString()
    };

    const filename = 'reading-progress.json';
    const filepath = path.join(dataDir, filename);

    await fs.writeFile(filepath, JSON.stringify(progressData, null, 2));

    console.log(`Reading progress saved: ${location}`);
    res.json({ success: true, message: 'Progress saved successfully' });
  } catch (error) {
    console.error('Error saving progress:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Load reading progress
app.get('/api/load-progress', async (req, res) => {
  try {
    const filepath = path.join(dataDir, 'reading-progress.json');

    try {
      const data = await fs.readFile(filepath, 'utf8');
      const progressData = JSON.parse(data);
      res.json({ success: true, data: progressData });
    } catch (fileError) {
      // File doesn't exist yet
      res.json({ success: true, data: null });
    }
  } catch (error) {
    console.error('Error loading progress:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Save mark
app.post('/api/save-mark', async (req, res) => {
  try {
    const markData = req.body;
    const filename = 'marks.json';
    const filepath = path.join(dataDir, filename);

    // Load existing marks
    let marks = [];
    try {
      const existingData = await fs.readFile(filepath, 'utf8');
      marks = JSON.parse(existingData);
    } catch (fileError) {
      // File doesn't exist yet, start with empty array
    }

    // Add new mark
    marks.push(markData);

    // Save updated marks
    await fs.writeFile(filepath, JSON.stringify(marks, null, 2));

    console.log(`Mark saved: "${markData.text.substring(0, 50)}..."`);
    res.json({ success: true, message: 'Mark saved successfully' });
  } catch (error) {
    console.error('Error saving mark:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Load marks
app.get('/api/load-marks', async (req, res) => {
  try {
    const filepath = path.join(dataDir, 'marks.json');

    try {
      const data = await fs.readFile(filepath, 'utf8');
      const marks = JSON.parse(data);
      res.json({ success: true, data: marks });
    } catch (fileError) {
      // File doesn't exist yet
      res.json({ success: true, data: [] });
    }
  } catch (error) {
    console.error('Error loading marks:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Update marks (for deletions)
app.post('/api/update-marks', async (req, res) => {
  try {
    const { marks } = req.body;
    const filename = 'marks.json';
    const filepath = path.join(dataDir, filename);

    // Save updated marks array
    await fs.writeFile(filepath, JSON.stringify(marks, null, 2));

    console.log(`Marks updated, ${marks.length} marks remaining`);
    res.json({ success: true, message: 'Marks updated successfully' });
  } catch (error) {
    console.error('Error updating marks:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Save note
app.post('/api/save-note', async (req, res) => {
  try {
    const noteData = req.body;
    const filename = 'notes.json';
    const filepath = path.join(dataDir, filename);

    // Load existing notes
    let notes = [];
    try {
      const existingData = await fs.readFile(filepath, 'utf8');
      notes = JSON.parse(existingData);
    } catch (fileError) {
      // File doesn't exist yet, start with empty array
    }

    // Add new note
    notes.push(noteData);

    // Save updated notes
    await fs.writeFile(filepath, JSON.stringify(notes, null, 2));

    console.log(`Note saved: "${noteData.text.substring(0, 50)}..." (${noteData.type})`);
    res.json({ success: true, message: 'Note saved successfully' });
  } catch (error) {
    console.error('Error saving note:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Load notes
app.get('/api/load-notes', async (req, res) => {
  try {
    const filepath = path.join(dataDir, 'notes.json');

    try {
      const data = await fs.readFile(filepath, 'utf8');
      const notes = JSON.parse(data);
      res.json({ success: true, data: notes });
    } catch (fileError) {
      // File doesn't exist yet
      res.json({ success: true, data: [] });
    }
  } catch (error) {
    console.error('Error loading notes:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Update notes (for deletions/undo)
app.post('/api/update-notes', async (req, res) => {
  try {
    const { notes } = req.body;
    const filename = 'notes.json';
    const filepath = path.join(dataDir, filename);

    // Save updated notes array
    await fs.writeFile(filepath, JSON.stringify(notes, null, 2));

    console.log(`Notes updated, ${notes.length} notes remaining`);
    res.json({ success: true, message: 'Notes updated successfully' });
  } catch (error) {
    console.error('Error updating notes:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`File server running on http://localhost:${PORT}`);
  console.log(`Data will be saved to: ${dataDir}`);
});