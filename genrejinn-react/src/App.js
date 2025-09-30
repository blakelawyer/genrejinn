import React, { useState, useEffect } from 'react';
import { ReactReader, ReactReaderStyle } from 'react-reader';
import { FaHeart, FaStar, FaBookmark, FaHighlighter, FaUnderline, FaTrash, FaChevronLeft, FaChevronRight, FaEdit } from 'react-icons/fa';
import { MdSettings, MdEdit } from 'react-icons/md';
import { LuZoomIn, LuZoomOut } from 'react-icons/lu';
import { IoColorPalette } from 'react-icons/io5';
import { GrUndo } from 'react-icons/gr';
import { akira } from './colors/akira';
import './App.css';

function App() {
  const [location, setLocation] = useState(null);
  const [fontSize, setFontSize] = useState(32);
  const [rendition, setRendition] = useState(null);
  const [currentColor, setCurrentColor] = useState(akira.foreground);
  const [currentSelection, setCurrentSelection] = useState(null);
  const [highlights, setHighlights] = useState([]);
  const [progress, setProgress] = useState(0);
  const [marks, setMarks] = useState([]);
  const [hoveredMark, setHoveredMark] = useState(null);
  const [notes, setNotes] = useState([]);
  const [expandedMarks, setExpandedMarks] = useState(new Set());
  const [editMode, setEditMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [currentResultIndex, setCurrentResultIndex] = useState(0);
  const [prevResults, setPrevResults] = useState([]);
  const [editingMarkId, setEditingMarkId] = useState(null);
  const [editingMarkTextId, setEditingMarkTextId] = useState(null);
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [tempMarkName, setTempMarkName] = useState('');
  const [tempMarkText, setTempMarkText] = useState('');
  const [tempNoteText, setTempNoteText] = useState('');

  const colors = [akira.foreground, akira.yellow, akira.green, akira.red, akira.blue, akira.white];
  const colorIndex = colors.indexOf(currentColor);

  const cycleColor = () => {
    const nextIndex = (colorIndex + 1) % colors.length;
    setCurrentColor(colors[nextIndex]);
  };

  const toggleEditMode = () => {
    setEditMode(prev => !prev);
  };

  const goToNextResult = () => {
    if (!searchResults.length) return;
    const nextIndex = (currentResultIndex + 1) % searchResults.length;
    setCurrentResultIndex(nextIndex);
    setLocation(searchResults[nextIndex].cfi);
  };

  const goToPreviousResult = () => {
    if (!searchResults.length) return;
    const prevIndex = (currentResultIndex - 1 + searchResults.length) % searchResults.length;
    setCurrentResultIndex(prevIndex);
    setLocation(searchResults[prevIndex].cfi);
  };

  const highlightSearchResults = (results) => {
    if (!rendition) return;
    results.forEach((result) => {
      rendition.annotations.add('highlight', result.cfi);
    });
  };

  const clearHighlights = () => {
    if (!rendition) return;
    prevResults.forEach((result) => {
      rendition.annotations.remove(result.cfi, 'highlight');
    });
  };

  const saveProgress = async (newLocation) => {
    try {
      await fetch('http://localhost:3001/api/save-progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ location: newLocation }),
      });
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/load-progress');
      const result = await response.json();
      if (result.success && result.data) {
        setLocation(result.data.location);
      }
    } catch (error) {
      console.error('Error loading progress:', error);
    }
  };

  const saveMark = async (markData) => {
    try {
      await fetch('http://localhost:3001/api/save-mark', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(markData),
      });
    } catch (error) {
      console.error('Error saving mark:', error);
    }
  };

  const loadMarks = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/load-marks');
      const result = await response.json();
      if (result.success && result.data) {
        setMarks(result.data);
      }
    } catch (error) {
      console.error('Error loading marks:', error);
    }
  };

  const saveNote = async (noteData) => {
    try {
      await fetch('http://localhost:3001/api/save-note', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(noteData),
      });
    } catch (error) {
      console.error('Error saving note:', error);
    }
  };

  const loadNotes = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/load-notes');
      const result = await response.json();
      if (result.success && result.data) {
        setNotes(result.data);
      }
    } catch (error) {
      console.error('Error loading notes:', error);
    }
  };

  const updateNotes = async (updatedNotes) => {
    try {
      await fetch('http://localhost:3001/api/update-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: updatedNotes }),
      });
    } catch (error) {
      console.error('Error updating notes:', error);
    }
  };


  useEffect(() => {
    loadProgress();
    loadMarks();
    loadNotes();
  }, []);


  const addMark = () => {
    console.log('Mark button clicked!');
    console.log('Current selection:', currentSelection);

    if (currentSelection && rendition) {
      const episodeNumber = marks.length + 1;
      const markData = {
        id: `mark-${Date.now()}`,
        cfiRange: currentSelection.cfiRange,
        text: currentSelection.text,
        name: `Episode ${episodeNumber}`,
        markText: '',
        timestamp: Date.now(),
        createdAt: new Date().toISOString()
      };

      console.log('Adding mark:', markData);

      // Add to local state
      setMarks(prev => [...prev, markData]);

      // Save to server
      saveMark(markData);

      // Clear selection after marking
      const selection = currentSelection.contents.window.getSelection();
      selection?.removeAllRanges();
      setCurrentSelection(null);
    } else {
      console.log('No text selected for marking');
    }
  };

  const navigateToMark = (mark) => {
    console.log('Navigating to mark:', mark);
    if (rendition && mark.cfiRange) {
      rendition.display(mark.cfiRange);
      setLocation(mark.cfiRange);
    }
  };

  const saveMarkName = async (markId, newName) => {
    console.log('Saving mark name:', markId, newName);

    // Update local state
    const updatedMarks = marks.map(mark =>
      mark.id === markId ? { ...mark, name: newName } : mark
    );
    setMarks(updatedMarks);

    // Save to server
    try {
      await fetch('http://localhost:3001/api/update-marks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ marks: updatedMarks }),
      });
    } catch (error) {
      console.error('Error saving mark name:', error);
    }
  };

  const saveNoteText = async (noteId, newNoteText) => {
    console.log('Saving note text:', noteId, newNoteText);

    // Update local state
    const updatedNotes = notes.map(note =>
      note.id === noteId ? { ...note, noteText: newNoteText } : note
    );
    setNotes(updatedNotes);

    // Save to server
    try {
      await fetch('http://localhost:3001/api/update-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: updatedNotes }),
      });
    } catch (error) {
      console.error('Error saving note text:', error);
    }
  };

  const saveMarkText = async (markId, newMarkText) => {
    console.log('Saving mark text:', markId, newMarkText);

    // Update local state
    const updatedMarks = marks.map(mark =>
      mark.id === markId ? { ...mark, markText: newMarkText } : mark
    );
    setMarks(updatedMarks);

    // Save to server
    try {
      await fetch('http://localhost:3001/api/update-marks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ marks: updatedMarks }),
      });
    } catch (error) {
      console.error('Error saving mark text:', error);
    }
  };

  const findParentMark = (noteCfiRange) => {
    if (!rendition || !rendition.book || !rendition.book.locations.total) {
      console.log('Locations not ready yet');
      return null;
    }

    const notePosition = rendition.book.locations.percentageFromCfi(noteCfiRange);
    if (notePosition === null) {
      console.log('Could not get position for note CFI');
      return null;
    }

    // Find the most recent mark before this note
    let parentMark = null;
    let closestDistance = Infinity;

    for (const mark of marks) {
      const markPosition = rendition.book.locations.percentageFromCfi(mark.cfiRange);
      if (markPosition !== null && markPosition <= notePosition) {
        const distance = notePosition - markPosition;
        if (distance < closestDistance) {
          closestDistance = distance;
          parentMark = mark;
        }
      }
    }

    return parentMark;
  };

  const toggleMarkExpansion = (markId, event) => {
    event.stopPropagation(); // Prevent navigation when toggling
    setExpandedMarks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(markId)) {
        newSet.delete(markId);
      } else {
        newSet.add(markId);
      }
      return newSet;
    });
  };



  const deleteNote = async (noteId) => {
    console.log('Deleting note:', noteId);

    const noteToDelete = notes.find(note => note.id === noteId);
    if (!noteToDelete) {
      console.log('Note not found');
      return;
    }

    // Remove visual styling from the epub
    if (rendition) {
      try {
        const currentContents = rendition.getContents();
        currentContents.forEach((contents) => {
          const spanElement = contents.document.querySelector(`.${noteId}`);
          if (spanElement) {
            console.log('Found span to remove:', spanElement);
            const parent = spanElement.parentNode;
            if (parent) {
              while (spanElement.firstChild) {
                parent.insertBefore(spanElement.firstChild, spanElement);
              }
              parent.removeChild(spanElement);
              console.log('Successfully removed styling');
            }
          }
        });
      } catch (error) {
        console.error('Error removing styling:', error);
      }
    }

    // Remove from local state
    const updatedNotes = notes.filter(note => note.id !== noteId);
    setNotes(updatedNotes);

    // Update server
    try {
      await fetch('http://localhost:3001/api/update-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: updatedNotes }),
      });
    } catch (error) {
      console.error('Error deleting note:', error);
    }
  };

  const deleteMarkWithReassignment = async (markId, event) => {
    event.stopPropagation(); // Prevent navigation when clicking delete
    console.log('Deleting mark:', markId);

    // Find all notes belonging to this mark
    const orphanedNotes = notes.filter(note => note.markId === markId);
    console.log('Notes to reassign:', orphanedNotes);

    // Reassign each note to new parent mark
    const updatedNotes = notes.map(note => {
      if (note.markId === markId) {
        // This note belonged to the deleted mark, find new parent
        const newParentMark = findParentMark(note.cfiRange);
        return {
          ...note,
          markId: newParentMark ? newParentMark.id : null
        };
      }
      return note;
    });

    // Remove mark from local state
    setMarks(prev => prev.filter(mark => mark.id !== markId));

    // Update notes with new assignments
    setNotes(updatedNotes);

    // Save updated marks and notes to server
    try {
      const updatedMarks = marks.filter(mark => mark.id !== markId);
      await fetch('http://localhost:3001/api/update-marks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ marks: updatedMarks }),
      });

      await fetch('http://localhost:3001/api/update-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: updatedNotes }),
      });
    } catch (error) {
      console.error('Error deleting mark:', error);
    }
  };

  useEffect(() => {
    if (rendition) {
      rendition.themes.fontSize(`${fontSize}px`);
    }
  }, [fontSize, rendition]);

  useEffect(() => {
    if (rendition) {
      function handleSelection(cfiRange, contents) {
        console.log('Selection detected!', cfiRange);
        if (rendition) {
          const selectedText = rendition.getRange(cfiRange).toString();
          console.log('Selected text:', selectedText);
          setCurrentSelection({ cfiRange, text: selectedText, contents });
        }
      }

      // Listen for selection events
      rendition.on('selected', handleSelection);

      // Also try removing any existing highlight styles
      rendition.hooks.content.register((contents) => {
        const document = contents.window.document;
        if (document) {
          const css = `
            .epubjs-hl {
              background-color: transparent !important;
              border: none !important;
            }
          `;
          const style = document.createElement('style');
          style.appendChild(document.createTextNode(css));
          document.head.appendChild(style);
        }
      });

      return () => {
        rendition?.off('selected', handleSelection);
      };
    }
  }, [rendition]);

  useEffect(() => {
    if (searchResults.length) {
      // Sort results by page order using CFI comparison
      const sortedResults = [...searchResults].sort((a, b) => {
        if (rendition && rendition.book) {
          const percentageA = rendition.book.locations.percentageFromCfi(a.cfi) || 0;
          const percentageB = rendition.book.locations.percentageFromCfi(b.cfi) || 0;
          return percentageA - percentageB;
        }
        return 0;
      });

      setLocation(sortedResults[0].cfi);
      setCurrentResultIndex(0);
      clearHighlights();
      highlightSearchResults(sortedResults);
      setPrevResults(sortedResults);

      // Update the searchResults state with sorted results
      if (JSON.stringify(sortedResults) !== JSON.stringify(searchResults)) {
        setSearchResults(sortedResults);
      }
    } else {
      clearHighlights();
      setPrevResults([]);
    }
  }, [searchResults]);

  const addHighlight = () => {
    console.log('Highlight button clicked!');
    console.log('Current selection:', currentSelection);
    console.log('Current color:', currentColor);

    if (currentSelection && rendition) {
      // Find parent mark
      const parentMark = findParentMark(currentSelection.cfiRange);

      if (!parentMark) {
        console.log('No mark found before this selection. Please create a mark first.');
        alert('Please create a mark (bookmark) before adding highlights. Marks organize your notes.');
        return;
      }

      const noteId = `note-${Date.now()}`;

      // Apply styling to the epub text
      try {
        const range = rendition.getRange(currentSelection.cfiRange);
        if (range) {
          const span = currentSelection.contents.window.document.createElement('span');
          span.style.color = currentColor;
          span.className = noteId;

          try {
            range.surroundContents(span);
            console.log('Successfully applied highlight color');
          } catch (e) {
            console.log('Surround failed, trying extractContents method');
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
          }
        }
      } catch (error) {
        console.error('Error applying highlight:', error);
      }

      const noteData = {
        id: noteId,
        text: currentSelection.text,
        cfiRange: currentSelection.cfiRange,
        color: currentColor,
        type: 'highlight',
        markId: parentMark.id,
        noteText: '',
        timestamp: Date.now(),
        createdAt: new Date().toISOString()
      };

      console.log('Creating note:', noteData);

      // Add to local state
      setNotes(prev => [...prev, noteData]);

      // Automatically expand the parent mark
      setExpandedMarks(prev => {
        const newSet = new Set(prev);
        newSet.add(parentMark.id);
        return newSet;
      });

      // Save to server
      saveNote(noteData);

      // Clear selection after creating note
      const selection = currentSelection.contents.window.getSelection();
      selection?.removeAllRanges();
      setCurrentSelection(null);
    }
  };

  const undoLastHighlight = () => {
    console.log('Undo button clicked!');
    console.log('Current notes:', notes);

    if (notes.length > 0) {
      const lastNote = notes[notes.length - 1];
      console.log('Removing note:', lastNote);

      // Remove styling from the epub
      if (rendition) {
        try {
          const currentContents = rendition.getContents();
          currentContents.forEach((contents) => {
            const spanElement = contents.document.querySelector(`.${lastNote.id}`);
            if (spanElement) {
              console.log('Found span to remove:', spanElement);
              const parent = spanElement.parentNode;
              if (parent) {
                while (spanElement.firstChild) {
                  parent.insertBefore(spanElement.firstChild, spanElement);
                }
                parent.removeChild(spanElement);
                console.log('Successfully removed styling');
              }
            }
          });
        } catch (error) {
          console.error('Error removing styling:', error);
        }
      }

      // Remove from local state
      const updatedNotes = notes.slice(0, -1);
      setNotes(updatedNotes);

      // Update server
      updateNotes(updatedNotes);
    } else {
      console.log('No notes to undo');
    }
  };

  const applyFormatting = (formatType) => {
    console.log(`${formatType} button clicked!`);
    console.log('Current selection:', currentSelection);
    console.log('Current color:', currentColor);

    if (currentSelection && rendition) {
      // Find parent mark
      const parentMark = findParentMark(currentSelection.cfiRange);

      if (!parentMark) {
        console.log('No mark found before this selection. Please create a mark first.');
        alert('Please create a mark (bookmark) before adding underlines. Marks organize your notes.');
        return;
      }

      const noteId = `note-${Date.now()}`;

      // Apply styling to the epub text
      try {
        const range = rendition.getRange(currentSelection.cfiRange);
        if (range) {
          const span = currentSelection.contents.window.document.createElement('span');
          span.className = noteId;
          span.style.textDecoration = 'underline';
          span.style.textDecorationColor = currentColor;

          try {
            range.surroundContents(span);
            console.log('Successfully applied underline');
          } catch (e) {
            console.log('Surround failed, trying extractContents method');
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
          }
        }
      } catch (error) {
        console.error('Error applying underline:', error);
      }

      const noteData = {
        id: noteId,
        text: currentSelection.text,
        cfiRange: currentSelection.cfiRange,
        color: currentColor,
        type: formatType, // 'underline'
        markId: parentMark.id,
        noteText: '',
        timestamp: Date.now(),
        createdAt: new Date().toISOString()
      };

      console.log('Creating note:', noteData);

      // Add to local state
      setNotes(prev => [...prev, noteData]);

      // Automatically expand the parent mark
      setExpandedMarks(prev => {
        const newSet = new Set(prev);
        newSet.add(parentMark.id);
        return newSet;
      });

      // Save to server
      saveNote(noteData);

      // Clear selection after creating note
      const selection = currentSelection.contents.window.getSelection();
      selection?.removeAllRanges();
      setCurrentSelection(null);
    }
  };

  const customStyles = {
    ...ReactReaderStyle,
    readerArea: {
      ...ReactReaderStyle.readerArea,
      backgroundColor: akira.background
    },
    arrow: {
      ...ReactReaderStyle.arrow,
      color: akira.foreground,
      fill: akira.foreground
    },
    arrowHover: {
      ...ReactReaderStyle.arrowHover,
      color: akira.foreground,
      fill: akira.foreground
    },
    tocArea: {
      ...ReactReaderStyle.tocArea,
      backgroundColor: akira.background,
      color: akira.foreground,
      border: `1px solid ${akira.foreground}`
    },
    tocButton: {
      ...ReactReaderStyle.tocButton,
      backgroundColor: akira.background,
      color: akira.foreground,
      border: `1px solid ${akira.foreground}`,
      outline: 'none'
    },
    tocButtonExpanded: {
      ...ReactReaderStyle.tocButtonExpanded,
      backgroundColor: akira.background,
      color: akira.foreground,
      border: `1px solid ${akira.foreground}`,
      outline: 'none'
    },
    tocButtonBar: {
      ...ReactReaderStyle.tocButtonBar,
      backgroundColor: akira.background,
      borderBottom: `1px solid ${akira.foreground}`
    }
  };

  return (
    <div className="App" style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: akira.background,
      gap: '20px'
    }}>
      {/* Search bar */}
      <div style={{
        position: 'fixed',
        top: '3.75vh',
        left: 'calc(50% - 40% / 6)',
        width: 'calc(40% / 3)',
        height: '32px',
        backgroundColor: akira.background,
        border: `2px solid ${akira.foreground}`,
        display: 'flex',
        alignItems: 'center',
        zIndex: 1000,
        padding: '4px'
      }}>
        <button
          onClick={goToPreviousResult}
          disabled={!searchResults.length}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            cursor: searchResults.length ? 'pointer' : 'default',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: searchResults.length ? 1 : 0.3
          }}
        >
          <FaChevronLeft color={akira.foreground} size={14} />
        </button>
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            backgroundColor: akira.background,
            color: akira.foreground,
            border: 'none',
            outline: 'none',
            padding: '4px 8px',
            fontSize: '14px',
            fontFamily: 'inherit'
          }}
        />
        <span style={{
          color: akira.foreground,
          fontSize: '12px',
          padding: '0 8px',
          whiteSpace: 'nowrap',
          opacity: searchResults.length ? 1 : 0.3
        }}>
          {searchResults.length > 0 ? `${currentResultIndex + 1}/${searchResults.length}` : '0/0'}
        </span>
        <button
          onClick={goToNextResult}
          disabled={!searchResults.length}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            cursor: searchResults.length ? 'pointer' : 'default',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: searchResults.length ? 1 : 0.3
          }}
        >
          <FaChevronRight color={akira.foreground} size={14} />
        </button>
      </div>
      <div style={{
        width: '3%',
        height: 'auto',
        border: `4px solid ${akira.foreground}`,
        backgroundColor: akira.background,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        alignSelf: 'center',
        gap: '10px',
        padding: '10px 0'
      }}>
          <button
            onClick={addMark}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <FaBookmark size="100%" color={akira.foreground} />
          </button>
          <button
            onClick={toggleEditMode}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <MdEdit size="100%" color={editMode ? akira.yellow : akira.foreground} />
          </button>
          <button
            onClick={cycleColor}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <IoColorPalette size="100%" color={currentColor} />
          </button>
          <button
            onClick={addHighlight}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <FaHighlighter size="100%" color={akira.foreground} />
          </button>
          <button
            onClick={() => applyFormatting('underline')}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <FaUnderline size="100%" color={akira.foreground} />
          </button>
          <button
            onClick={() => setFontSize(prev => Math.max(10, prev - 2))}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <LuZoomOut size="100%" color={akira.foreground} />
          </button>
          <button
            onClick={() => setFontSize(prev => Math.min(50, prev + 2))}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <LuZoomIn size="100%" color={akira.foreground} />
          </button>
          <button
            onClick={undoLastHighlight}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              width: '100%',
              height: '50px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <GrUndo size="100%" color={akira.foreground} />
          </button>
        </div>
      <div style={{
        width: '40%',
        height: '85%',
        aspectRatio: '1 / 1.414',
        border: `4px solid ${akira.foreground}`,
        backgroundColor: akira.background,
        position: 'relative',
        boxSizing: 'border-box'
      }}>
        <ReactReader
          url="/gravitys-rainbow.epub"
          location={location}
          locationChanged={(epubcfi) => {
            setLocation(epubcfi);
            saveProgress(epubcfi);

            // Calculate progress percentage
            if (rendition && rendition.book && rendition.book.locations.total > 0) {
              const percentage = rendition.book.locations.percentageFromCfi(epubcfi);
              console.log('Progress updated:', percentage, 'for CFI:', epubcfi);
              setProgress(percentage || 0);
            }
          }}
          showToc={false}
          title=""
          searchQuery={searchQuery}
          onSearchResults={setSearchResults}
          readerStyles={customStyles}
          epubOptions={{
            flow: 'paginated',
            manager: 'default',
            allowScriptedContent: false,
            snap: false
          }}
          getRendition={(renditionObj) => {
            setRendition(renditionObj);
            renditionObj.themes.default({
              body: {
                'background-color': akira.background,
                'color': akira.foreground
              }
            });
            renditionObj.themes.fontSize(`${fontSize}px`);
            renditionObj.spread('none'); // Force single column

            // Generate locations for progress calculation
            renditionObj.book.ready.then(() => {
              return renditionObj.book.locations.generate(1600);
            }).then(() => {
              console.log('Locations generated for progress tracking');
              // Update progress for current location if we have one
              if (location) {
                const percentage = renditionObj.book.locations.percentageFromCfi(location);
                console.log('Initial progress:', percentage);
                setProgress(percentage || 0);
              }
            });

            // Disable default highlighting and add custom styles
            renditionObj.hooks.content.register((contents) => {
              const document = contents.window.document;
              if (document) {
                // Detect the actual font being used
                setTimeout(() => {
                  const body = document.body;
                  const firstParagraph = document.querySelector('p') || body;
                  if (firstParagraph) {
                    const computedStyle = contents.window.getComputedStyle(firstParagraph);
                    if (computedStyle) {
                      console.log('EPUB Font Family:', computedStyle.fontFamily);
                      console.log('EPUB Font Size:', computedStyle.fontSize);
                      console.log('EPUB Font Weight:', computedStyle.fontWeight);
                      console.log('EPUB Line Height:', computedStyle.lineHeight);

                      // Store the detected font family globally so we can use it
                      window.epubFontFamily = computedStyle.fontFamily;
                      window.epubFontSize = computedStyle.fontSize;
                    }
                  }
                }, 100);

                const css = `
                  *::selection {
                    background-color: ${akira.foreground} !important;
                    color: ${akira.background} !important;
                  }
                  *::-moz-selection {
                    background-color: ${akira.foreground} !important;
                    color: ${akira.background} !important;
                  }
                  .epubjs-hl {
                    background: none !important;
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                  }
                  a, a:link, a:visited {
                    color: ${akira.blue} !important;
                    text-decoration: underline !important;
                    text-decoration-color: ${akira.blue} !important;
                  }
                  a:hover {
                    color: ${akira.yellow} !important;
                    text-decoration-color: ${akira.yellow} !important;
                  }
                  a:active {
                    color: ${akira.red} !important;
                    text-decoration-color: ${akira.red} !important;
                  }
                `;
                const style = document.createElement('style');
                style.appendChild(document.createTextNode(css));
                document.head.appendChild(style);

                // Allow selection events to work properly
              }
            });
          }}
        />
        {/* Progress bar */}
        <div style={{
          position: 'fixed',
          bottom: '3.75vh',
          left: 'calc(50% - 20%)',
          width: '40%',
          height: '8px',
          backgroundColor: akira.background,
          border: `2px solid ${akira.foreground}`,
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${progress * 100}%`,
            height: '100%',
            backgroundColor: akira.foreground,
            transition: 'width 0.3s ease'
          }}></div>
        </div>
      </div>
      <div style={{
        width: '40%',
        height: '85%',
        aspectRatio: '1 / 1.414',
        border: `4px solid ${akira.foreground}`,
        backgroundColor: akira.background,
        padding: '20px',
        overflowY: 'auto',
        boxSizing: 'border-box'
      }}>
        {/* Orphaned Notes Section */}
        {(() => {
          const markIds = new Set(marks.map(m => m.id));
          const orphanedNotes = notes.filter(note => !note.markId || !markIds.has(note.markId));
          const isOrphanedExpanded = expandedMarks.has('orphaned');

          if (orphanedNotes.length === 0) return null;

          return (
            <div
              style={{
                backgroundColor: akira.background,
                border: `1px solid ${akira.foreground}`,
                marginBottom: '10px',
                borderRadius: '4px',
                overflow: 'hidden'
              }}
            >
              {/* Orphaned header */}
              <div
                onMouseEnter={() => setHoveredMark('orphaned')}
                onMouseLeave={() => setHoveredMark(null)}
                style={{
                  padding: '10px',
                  color: akira.foreground,
                  fontSize: `${fontSize}px`,
                  fontFamily: 'serif',
                  opacity: (hoveredMark === 'orphaned' || isOrphanedExpanded) ? 1 : 0.6,
                  transition: 'opacity 0.3s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '10px'
                }}
              >
                {/* Dropdown arrow on left */}
                <span
                  onClick={(e) => toggleMarkExpansion('orphaned', e)}
                  style={{
                    fontSize: `${(fontSize + 20) / 2}px`,
                    lineHeight: '1',
                    width: `${(fontSize + 20) / 2}px`,
                    height: `${(fontSize + 20) / 2}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    cursor: 'pointer'
                  }}>
                  {isOrphanedExpanded ? '▼' : '▶'}
                </span>

                {/* Title in center */}
                <span style={{
                  flex: 1,
                  textAlign: 'center'
                }}>
                  Unorganized Notes
                </span>

                {/* Note count on right */}
                <span style={{
                  fontSize: `${(fontSize + 20) / 2}px`,
                  lineHeight: '1',
                  width: `${(fontSize + 20) / 2}px`,
                  height: `${(fontSize + 20) / 2}px`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  ({orphanedNotes.length})
                </span>
              </div>

              {/* Orphaned notes list (shown when expanded) */}
              {isOrphanedExpanded && (
                <div style={{
                  borderTop: `1px solid ${akira.foreground}`,
                  padding: '10px',
                  maxHeight: '300px',
                  overflowY: 'auto'
                }}>
                  {orphanedNotes.map(note => (
                    <div
                      key={note.id}
                      style={{
                        padding: '8px',
                        marginBottom: '8px',
                        backgroundColor: akira.background,
                        border: `1px solid ${akira.foreground}`,
                        borderRadius: '2px',
                        fontSize: `${fontSize * 0.75}px`,
                        fontFamily: 'serif',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px'
                      }}
                    >
                      {/* Top row: icons and note text */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '8px'
                      }}>
                        {editMode && (
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingNoteId(note.id);
                              setTempNoteText(note.noteText || '');
                            }}
                            style={{
                              cursor: 'pointer',
                              flexShrink: 0,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <FaEdit color={akira.yellow} size="0.8em" />
                          </span>
                        )}
                        <span style={{
                          flex: 1,
                          ...(note.type === 'highlight' ? {
                            color: note.color
                          } : {
                            color: akira.foreground,
                            textDecoration: 'underline',
                            textDecorationColor: note.color
                          })
                        }}>
                          {note.text}
                        </span>
                        {editMode && (
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteNote(note.id);
                            }}
                            style={{
                              cursor: 'pointer',
                              flexShrink: 0,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <FaTrash color={akira.red} size="0.8em" />
                          </span>
                        )}
                      </div>
                      {/* Textarea for note text (editing or displaying) */}
                      {(editingNoteId === note.id || (note.noteText && note.noteText.trim() !== '')) && (
                        editingNoteId === note.id ? (
                          <textarea
                            value={tempNoteText}
                            onChange={(e) => setTempNoteText(e.target.value)}
                            onBlur={() => {
                              saveNoteText(note.id, tempNoteText);
                              setEditingNoteId(null);
                            }}
                            placeholder="Add your notes here..."
                            autoFocus
                            style={{
                              width: '100%',
                              minHeight: '60px',
                              backgroundColor: akira.background,
                              color: akira.foreground,
                              border: `1px solid ${akira.yellow}`,
                              outline: 'none',
                              fontSize: `${fontSize * 0.7}px`,
                              fontFamily: 'serif',
                              padding: '4px',
                              borderRadius: '2px',
                              resize: 'vertical'
                            }}
                          />
                        ) : (
                          <div style={{
                            width: '100%',
                            backgroundColor: akira.background,
                            color: akira.foreground,
                            fontSize: `${fontSize * 0.7}px`,
                            fontFamily: 'serif',
                            padding: '4px',
                            borderTop: `1px solid ${akira.foreground}`,
                            opacity: 0.8,
                            whiteSpace: 'pre-wrap'
                          }}>
                            {note.noteText}
                          </div>
                        )
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })()}

        {marks
          .sort((a, b) => {
            // Sort marks by their CFI position in the book
            if (rendition && rendition.book && rendition.book.locations.total > 0) {
              const percentageA = rendition.book.locations.percentageFromCfi(a.cfiRange) || 0;
              const percentageB = rendition.book.locations.percentageFromCfi(b.cfiRange) || 0;
              return percentageA - percentageB;
            }
            // Fallback to creation time if locations aren't available
            return a.timestamp - b.timestamp;
          })
          .map((mark, index) => {
            const markNotes = notes.filter(note => note.markId === mark.id);
            const isExpanded = expandedMarks.has(mark.id);

            return (
              <div
                key={mark.id}
                style={{
                  backgroundColor: akira.background,
                  border: `1px solid ${akira.foreground}`,
                  marginBottom: '10px',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}
              >
                {/* Mark header */}
                <div
                  onMouseEnter={() => setHoveredMark(mark.id)}
                  onMouseLeave={() => setHoveredMark(null)}
                  style={{
                    padding: '10px',
                    color: akira.foreground,
                    fontSize: `${fontSize}px`,
                    fontFamily: 'serif',
                    opacity: (hoveredMark === mark.id || isExpanded) ? 1 : 0.6,
                    transition: 'opacity 0.3s ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '10px'
                  }}
                >
                  {/* Left group: Dropdown arrow and Edit icon */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    flexShrink: 0
                  }}>
                    {/* Dropdown arrow on left */}
                    <span
                      onClick={(e) => toggleMarkExpansion(mark.id, e)}
                      style={{
                        fontSize: `${(fontSize + 20) / 2}px`,
                        lineHeight: '1',
                        width: `${(fontSize + 20) / 2}px`,
                        height: `${(fontSize + 20) / 2}px`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        cursor: 'pointer'
                      }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>

                    {/* Edit icon (only in edit mode when expanded) */}
                    {editMode && isExpanded && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingMarkTextId(mark.id);
                          setTempMarkText(mark.markText || '');
                        }}
                        style={{
                          fontSize: `${(fontSize + 20) / 2}px`,
                          lineHeight: '1',
                          width: `${(fontSize + 20) / 2}px`,
                          height: `${(fontSize + 20) / 2}px`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          cursor: 'pointer'
                        }}
                      >
                        <FaEdit color={akira.yellow} size="70%" />
                      </span>
                    )}
                  </div>

                  {/* Mark name in center */}
                  {editingMarkId === mark.id ? (
                    <input
                      type="text"
                      value={tempMarkName}
                      onChange={(e) => setTempMarkName(e.target.value)}
                      onBlur={() => {
                        saveMarkName(mark.id, tempMarkName);
                        setEditingMarkId(null);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          saveMarkName(mark.id, tempMarkName);
                          setEditingMarkId(null);
                        } else if (e.key === 'Escape') {
                          setEditingMarkId(null);
                        }
                      }}
                      autoFocus
                      style={{
                        flex: 1,
                        textAlign: 'center',
                        backgroundColor: akira.background,
                        color: akira.foreground,
                        border: `1px solid ${akira.yellow}`,
                        outline: 'none',
                        fontSize: `${fontSize}px`,
                        fontFamily: 'serif',
                        padding: '2px 8px',
                        borderRadius: '2px'
                      }}
                    />
                  ) : (
                    <span
                      onClick={() => navigateToMark(mark)}
                      style={{
                        flex: 1,
                        textAlign: 'center',
                        cursor: 'pointer'
                      }}>
                      {mark.name || `Episode ${index + 1}`}
                    </span>
                  )}

                  {/* Right group: Trash icon and Note count */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    flexShrink: 0
                  }}>
                    {/* Trash icon (only in edit mode when expanded) */}
                    {editMode && isExpanded && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMarkWithReassignment(mark.id, e);
                        }}
                        style={{
                          fontSize: `${(fontSize + 20) / 2}px`,
                          lineHeight: '1',
                          width: `${(fontSize + 20) / 2}px`,
                          height: `${(fontSize + 20) / 2}px`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          cursor: 'pointer'
                        }}
                      >
                        <FaTrash color={akira.red} size="70%" />
                      </span>
                    )}

                    {/* Note count on right */}
                    <span style={{
                      fontSize: `${(fontSize + 20) / 2}px`,
                      lineHeight: '1',
                      width: `${(fontSize + 20) / 2}px`,
                      height: `${(fontSize + 20) / 2}px`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      ({markNotes.length})
                    </span>
                  </div>
                </div>

                {/* Mark textarea section (shown when expanded) */}
                {isExpanded && (editingMarkTextId === mark.id || (mark.markText && mark.markText.trim() !== '')) && (
                  <div style={{
                    borderTop: `1px solid ${akira.foreground}`,
                    padding: '10px',
                    backgroundColor: akira.background
                  }}>
                    {editingMarkTextId === mark.id ? (
                      <textarea
                        value={tempMarkText}
                        onChange={(e) => setTempMarkText(e.target.value)}
                        onBlur={() => {
                          saveMarkText(mark.id, tempMarkText);
                          setEditingMarkTextId(null);
                        }}
                        placeholder="Add summary or notes for this mark..."
                        autoFocus
                        style={{
                          width: '100%',
                          minHeight: '80px',
                          backgroundColor: akira.background,
                          color: akira.foreground,
                          border: `1px solid ${akira.yellow}`,
                          outline: 'none',
                          fontSize: `${fontSize * 0.8}px`,
                          fontFamily: 'serif',
                          padding: '8px',
                          borderRadius: '2px',
                          resize: 'vertical',
                          boxSizing: 'border-box'
                        }}
                      />
                    ) : (
                      <div style={{
                        width: '100%',
                        backgroundColor: akira.background,
                        color: akira.foreground,
                        fontSize: `${fontSize * 0.8}px`,
                        fontFamily: 'serif',
                        padding: '8px',
                        opacity: 0.9,
                        whiteSpace: 'pre-wrap'
                      }}>
                        {mark.markText}
                      </div>
                    )}
                  </div>
                )}

                {/* Notes list (shown when expanded) */}
                {isExpanded && markNotes.length > 0 && (
                  <div style={{
                    borderTop: `1px solid ${akira.foreground}`,
                    padding: '10px',
                    maxHeight: '300px',
                    overflowY: 'auto'
                  }}>
                    {markNotes.map(note => (
                      <div
                        key={note.id}
                        style={{
                          padding: '8px',
                          marginBottom: '8px',
                          backgroundColor: akira.background,
                          border: `1px solid ${akira.foreground}`,
                          borderRadius: '2px',
                          fontSize: `${fontSize * 0.75}px`,
                          fontFamily: 'serif',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px'
                        }}
                      >
                        {/* Top row: icons and note text */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '8px'
                        }}>
                          {editMode && (
                            <span
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingNoteId(note.id);
                                setTempNoteText(note.noteText || '');
                              }}
                              style={{
                                cursor: 'pointer',
                                flexShrink: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}
                            >
                              <FaEdit color={akira.yellow} size="0.8em" />
                            </span>
                          )}
                          <span style={{
                            flex: 1,
                            ...(note.type === 'highlight' ? {
                              color: note.color
                            } : {
                              color: akira.foreground,
                              textDecoration: 'underline',
                              textDecorationColor: note.color
                            })
                          }}>
                            {note.text}
                          </span>
                          {editMode && (
                            <span
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteNote(note.id);
                              }}
                              style={{
                                cursor: 'pointer',
                                flexShrink: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}
                            >
                              <FaTrash color={akira.red} size="0.8em" />
                            </span>
                          )}
                        </div>
                        {/* Textarea for note text (editing or displaying) */}
                        {(editingNoteId === note.id || (note.noteText && note.noteText.trim() !== '')) && (
                          editingNoteId === note.id ? (
                            <textarea
                              value={tempNoteText}
                              onChange={(e) => setTempNoteText(e.target.value)}
                              onBlur={() => {
                                saveNoteText(note.id, tempNoteText);
                                setEditingNoteId(null);
                              }}
                              placeholder="Add your notes here..."
                              autoFocus
                              style={{
                                width: '100%',
                                minHeight: '60px',
                                backgroundColor: akira.background,
                                color: akira.foreground,
                                border: `1px solid ${akira.yellow}`,
                                outline: 'none',
                                fontSize: `${fontSize * 0.7}px`,
                                fontFamily: 'serif',
                                padding: '4px',
                                borderRadius: '2px',
                                resize: 'vertical'
                              }}
                            />
                          ) : (
                            <div style={{
                              width: '100%',
                              backgroundColor: akira.background,
                              color: akira.foreground,
                              fontSize: `${fontSize * 0.7}px`,
                              fontFamily: 'serif',
                              padding: '4px',
                              borderTop: `1px solid ${akira.foreground}`,
                              opacity: 0.8,
                              whiteSpace: 'pre-wrap'
                            }}>
                              {note.noteText}
                            </div>
                          )
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        {marks.length === 0 && (
          <div style={{
            color: akira.foreground,
            fontSize: '14px',
            opacity: 0.6,
            textAlign: 'center',
            marginTop: '40px'
          }}>
            No marks yet. Select text and click the bookmark button to add marks.
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
