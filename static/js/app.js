document.addEventListener('DOMContentLoaded', () => {
  // ── Global State Variables ──
  let selectedFile = null;
  let selectedImages = [];
  let selectedFsPath = null;
  let activeTranscriptData = null;
  let currentFsPath = "";

  // ── DOM Elements ──
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabPanels = document.querySelectorAll('.tab-panel');
  const statusBadge = document.getElementById('statusBadge');

  // Input Tab Elements
  const ytUrlInput = document.getElementById('ytUrlInput');
  const ytSubmitBtn = document.getElementById('ytSubmitBtn');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const fileSelectedInfo = document.getElementById('fileSelectedInfo');
  const fileName = document.getElementById('fileName');
  const removeFileBtn = document.getElementById('removeFileBtn');

  // OCR Image Dropzone Elements
  const ocrDropzone = document.getElementById('ocrDropzone');
  const imageInput = document.getElementById('imageInput');
  const ocrDropzoneContent = document.getElementById('ocrDropzoneContent');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');
  const imagePreviewCount = document.getElementById('imagePreviewCount');
  const clearImagesBtn = document.getElementById('clearImagesBtn');
  const imageThumbnailsGrid = document.getElementById('imageThumbnailsGrid');

  const openFsModalBtn = document.getElementById('openFsModalBtn');
  const selectedFsPathDisplay = document.getElementById('selectedFsPathDisplay');
  const fsPathText = document.getElementById('fsPathText');
  const languageSelect = document.getElementById('languageSelect');
  const processBtn = document.getElementById('processBtn');

  // Progress Overlay
  const progressContainer = document.getElementById('progressContainer');
  const progressTitle = document.getElementById('progressTitle');
  const progressSubtitle = document.getElementById('progressSubtitle');
  const progressBar = document.getElementById('progressBar');

  // Dashboard Elements
  const meetingTitle = document.getElementById('meetingTitle');
  const metaSource = document.getElementById('metaSource');
  const metaWords = document.getElementById('metaWords');
  const metaLanguage = document.getElementById('metaLanguage');
  const summaryContent = document.getElementById('summaryContent');
  const transcriptContent = document.getElementById('transcriptContent');
  const transcriptSearch = document.getElementById('transcriptSearch');
  const copyTranscriptBtn = document.getElementById('copyTranscriptBtn');
  const exportTxtBtn = document.getElementById('exportTxtBtn');
  const exportJsonBtn = document.getElementById('exportJsonBtn');

  // Chat Elements
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const sendChatBtn = document.getElementById('sendChatBtn');
  const clearMemoryBtn = document.getElementById('clearMemoryBtn');
  const promptChips = document.querySelectorAll('.chip');

  // File System Modal Elements
  const fsModal = document.getElementById('fsModal');
  const closeFsModalBtn = document.getElementById('closeFsModalBtn');
  const cancelFsBtn = document.getElementById('cancelFsBtn');
  const confirmFsBtn = document.getElementById('confirmFsBtn');
  const currentPathText = document.getElementById('currentPathText');
  const fsDirectoryList = document.getElementById('fsDirectoryList');

  // ── 1. Tab Navigation ──
  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTabId = tab.getAttribute('data-tab');

      navTabs.forEach(t => t.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(targetTabId);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });

  // ── 2. Drag & Drop File Handling (Audio / Video) ──
  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('#removeFileBtn')) return;
    fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      if (files[0].type.startsWith('image/')) {
        handleImagesSelected(files);
      } else {
        handleFileSelected(files[0]);
      }
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      const f = e.target.files[0];
      if (f.type.startsWith('image/')) {
        handleImagesSelected([f]);
      } else {
        handleFileSelected(f);
      }
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    clearSelectedImages();
    selectedFsPath = null;
    selectedFsPathDisplay.classList.add('hidden');
    ytUrlInput.value = '';

    fileName.textContent = file.name;
    fileSelectedInfo.classList.remove('hidden');
    dropzone.querySelector('.dropzone-content').classList.add('hidden');
  }

  removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    fileSelectedInfo.classList.add('hidden');
    dropzone.querySelector('.dropzone-content').classList.remove('hidden');
  });

  // ── 3. OCR Image Dropzone & Multi-Image Handling ──
  if (ocrDropzone) {
    ocrDropzone.addEventListener('click', (e) => {
      if (e.target.closest('#clearImagesBtn') || e.target.closest('.image-thumb-remove')) return;
      imageInput.click();
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      ocrDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        ocrDropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      ocrDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        ocrDropzone.classList.remove('dragover');
      });
    });

    ocrDropzone.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/') || /\.(png|jpe?g|webp|bmp|tiff?)$/i.test(f.name));
      if (files.length > 0) {
        handleImagesSelected(files);
      } else {
        alert('Please drop valid image files (PNG, JPG, WEBP, BMP, TIFF).');
      }
    });

    imageInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleImagesSelected(Array.from(e.target.files));
      }
    });

    clearImagesBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearSelectedImages();
    });
  }

  function handleImagesSelected(newFiles) {
    // Clear other input modes
    selectedFile = null;
    fileInput.value = '';
    fileSelectedInfo.classList.add('hidden');
    dropzone.querySelector('.dropzone-content').classList.remove('hidden');

    selectedFsPath = null;
    selectedFsPathDisplay.classList.add('hidden');
    ytUrlInput.value = '';

    // Append new images without duplicates
    newFiles.forEach(f => {
      if (!selectedImages.some(existing => existing.name === f.name && existing.size === f.size)) {
        selectedImages.push(f);
      }
    });

    renderImagePreviews();
  }

  function clearSelectedImages() {
    selectedImages = [];
    if (imageInput) imageInput.value = '';
    if (imageThumbnailsGrid) imageThumbnailsGrid.innerHTML = '';
    if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
    if (ocrDropzoneContent) ocrDropzoneContent.classList.remove('hidden');
  }

  function renderImagePreviews() {
    if (selectedImages.length === 0) {
      clearSelectedImages();
      return;
    }

    ocrDropzoneContent.classList.add('hidden');
    imagePreviewContainer.classList.remove('hidden');

    imagePreviewCount.innerHTML = `<i class="fa-solid fa-images"></i> ${selectedImages.length} Image${selectedImages.length > 1 ? 's' : ''} Ready for OCR`;
    imageThumbnailsGrid.innerHTML = '';

    selectedImages.forEach((imgFile, index) => {
      const card = document.createElement('div');
      card.className = 'image-thumb-card';

      const objectUrl = URL.createObjectURL(imgFile);

      card.innerHTML = `
        <img src="${objectUrl}" alt="${imgFile.name}" />
        <button type="button" class="image-thumb-remove" title="Remove image">
          <i class="fa-solid fa-xmark"></i>
        </button>
        <div class="image-thumb-info">
          <div class="image-thumb-name" title="${imgFile.name}">${imgFile.name}</div>
          <div class="image-thumb-size">${formatBytes(imgFile.size)}</div>
        </div>
      `;

      card.querySelector('.image-thumb-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        selectedImages.splice(index, 1);
        URL.revokeObjectURL(objectUrl);
        renderImagePreviews();
      });

      imageThumbnailsGrid.appendChild(card);
    });
  }

  // ── 4. Server File System Browser Modal ──
  openFsModalBtn.addEventListener('click', () => {
    fsModal.classList.remove('hidden');
    loadFileSystemPath('');
  });

  closeFsModalBtn.addEventListener('click', () => fsModal.classList.add('hidden'));
  cancelFsBtn.addEventListener('click', () => fsModal.classList.add('hidden'));

  async function loadFileSystemPath(dirPath) {
    fsDirectoryList.innerHTML = '<div class="loading-spinner-sm">Loading directory contents...</div>';
    try {
      const url = dirPath ? `/api/filesystem?path=${encodeURIComponent(dirPath)}` : '/api/filesystem';
      const res = await fetch(url);
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Failed to fetch directory');

      currentFsPath = data.current_path;
      currentPathText.textContent = currentFsPath;
      renderFsItems(data.parent_path, data.items);
    } catch (err) {
      fsDirectoryList.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
    }
  }

  function renderFsItems(parentPath, items) {
    fsDirectoryList.innerHTML = '';
    confirmFsBtn.disabled = true;

    // Up directory item if parent exists
    if (parentPath !== null) {
      const parentItem = document.createElement('div');
      parentItem.className = 'fs-item';
      parentItem.innerHTML = `
        <div class="fs-item-name">
          <i class="fa-solid fa-folder-open" style="color:#f59e0b"></i>
          <span>.. (Up Directory)</span>
        </div>
      `;
      parentItem.addEventListener('click', () => loadFileSystemPath(parentPath));
      fsDirectoryList.appendChild(parentItem);
    }

    if (items.length === 0) {
      fsDirectoryList.innerHTML += '<div style="padding:10px; color:#64748b;">Directory is empty</div>';
      return;
    }

    items.forEach(item => {
      const div = document.createElement('div');
      div.className = 'fs-item';

      let iconClass = 'fa-file';
      let iconColor = '#64748b';
      let typeLabel = 'File';

      if (item.is_dir) {
        iconClass = 'fa-folder';
        iconColor = '#f59e0b';
        typeLabel = 'Folder';
      } else if (item.is_image) {
        iconClass = 'fa-file-image';
        iconColor = '#c084fc';
        typeLabel = 'Image';
      } else if (item.is_media) {
        iconClass = 'fa-file-audio';
        iconColor = '#06b6d4';
        typeLabel = 'Media';
      }

      div.innerHTML = `
        <div class="fs-item-name">
          <i class="fa-solid ${iconClass}" style="color:${iconColor}"></i>
          <span>${item.name}</span>
        </div>
        <span class="badge">${item.is_dir ? typeLabel : (item.size ? formatBytes(item.size) : typeLabel)}</span>
      `;

      div.addEventListener('click', () => {
        if (item.is_dir) {
          loadFileSystemPath(item.path);
        } else {
          document.querySelectorAll('.fs-item').forEach(el => el.classList.remove('selected'));
          div.classList.add('selected');
          selectedFsPath = item.path;
          confirmFsBtn.disabled = false;
        }
      });

      fsDirectoryList.appendChild(div);
    });
  }

  confirmFsBtn.addEventListener('click', () => {
    if (selectedFsPath) {
      selectedFile = null;
      fileSelectedInfo.classList.add('hidden');
      dropzone.querySelector('.dropzone-content').classList.remove('hidden');
      clearSelectedImages();
      ytUrlInput.value = '';

      fsPathText.textContent = selectedFsPath;
      selectedFsPathDisplay.classList.remove('hidden');
      fsModal.classList.add('hidden');
    }
  });

  // ── 5. Main Processing Action ──
  processBtn.addEventListener('click', () => startProcessing());
  ytSubmitBtn.addEventListener('click', () => startProcessing('yt'));

  async function startProcessing(forcedType = null) {
    const lang = languageSelect.value;
    let endpoint = '';
    let formData = new FormData();
    let payloadJson = {};

    const ytUrl = ytUrlInput.value.trim();

    if (forcedType === 'yt' || (ytUrl && !selectedFile && selectedImages.length === 0 && !selectedFsPath)) {
      if (!ytUrl) {
        alert('Please enter a valid YouTube URL');
        return;
      }
      endpoint = '/api/process/yt';
      payloadJson = { url: ytUrl, language: lang };
      showProgressOverlay('Downloading & Transcribing YouTube...', 'Extracting audio stream, running speech recognition, and building RAG index.');
    } else if (selectedImages.length > 0) {
      if (selectedImages.length === 1) {
        endpoint = '/api/process/upload';
        formData.append('file', selectedImages[0]);
        formData.append('language', 'english');
      } else {
        endpoint = '/api/process/images';
        selectedImages.forEach(img => formData.append('files', img));
      }
      showProgressOverlay('Extracting Text via PaddleOCR...', `Recognizing visual text across ${selectedImages.length} image(s), generating summary, and indexing into RAG.`);
    } else if (selectedFile) {
      const isImg = selectedFile.type.startsWith('image/') || /\.(png|jpe?g|webp|bmp|tiff?)$/i.test(selectedFile.name);
      endpoint = '/api/process/upload';
      formData.append('file', selectedFile);
      formData.append('language', lang);

      if (isImg) {
        showProgressOverlay('Running PaddleOCR...', 'Extracting text from image, creating summary, and indexing for AI chat.');
      } else {
        showProgressOverlay('Processing Media File...', 'Transcribing speech, summarizing key decisions, and building RAG index.');
      }
    } else if (selectedFsPath) {
      endpoint = '/api/process/filesystem';
      payloadJson = { path: selectedFsPath, language: lang };

      const isImg = /\.(png|jpe?g|webp|bmp|tiff?)$/i.test(selectedFsPath);
      if (isImg) {
        showProgressOverlay('Running PaddleOCR on Server Image...', 'Recognizing document text and creating RAG conversational index.');
      } else {
        showProgressOverlay('Processing Server File...', 'Transcribing audio/video, generating summary, and building RAG index.');
      }
    } else {
      alert('Please provide a YouTube URL, an audio/video file, an image for OCR, or choose a file from the server file system.');
      return;
    }

    updateStatus('status-processing', 'Processing...');

    try {
      let response;
      if (endpoint === '/api/process/upload' || endpoint === '/api/process/images') {
        response = await fetch(endpoint, { method: 'POST', body: formData });
      } else {
        response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadJson)
        });
      }

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Processing failed');

      activeTranscriptData = data;
      renderDashboard(data);

      hideProgressOverlay();
      updateStatus('status-ready', 'Indexed & Ready');

      // Switch to Dashboard Tab
      document.getElementById('dashboardTabBtn').click();
    } catch (err) {
      hideProgressOverlay();
      updateStatus('status-ready', 'System Ready');
      alert(`Processing Error: ${err.message}`);
    }
  }

  // ── 5. Render Dashboard & Summary ──
  function renderDashboard(data) {
    meetingTitle.textContent = data.title || 'Untitled Meeting Summary';
    metaSource.innerHTML = `<i class="fa-solid fa-link"></i> Source: ${data.source || 'Uploaded File'}`;
    metaWords.innerHTML = `<i class="fa-solid fa-font"></i> Words: ${data.word_count || 0}`;
    metaLanguage.innerHTML = `<i class="fa-solid fa-language"></i> Engine: ${data.language || 'Whisper'}`;

    // Simple markdown formatting replacement for bullet points / bold
    let formattedSummary = (data.summary || '')
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>');

    if (formattedSummary.includes('<li>')) {
      formattedSummary = `<ul>${formattedSummary}</ul>`;
    }

    summaryContent.innerHTML = formattedSummary || '<p>No summary generated.</p>';
    transcriptContent.textContent = data.transcript || 'No transcript text available.';
  }

  // Search Transcript Filter
  transcriptSearch.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    if (!activeTranscriptData || !activeTranscriptData.transcript) return;

    if (!query) {
      transcriptContent.textContent = activeTranscriptData.transcript;
      return;
    }

    const text = activeTranscriptData.transcript;
    const lines = text.split('\n');
    const filteredLines = lines.filter(line => line.toLowerCase().includes(query));
    transcriptContent.textContent = filteredLines.join('\n') || 'No matching lines found.';
  });

  // Copy Transcript
  copyTranscriptBtn.addEventListener('click', () => {
    if (!activeTranscriptData || !activeTranscriptData.transcript) return;
    navigator.clipboard.writeText(activeTranscriptData.transcript);
    const originalText = copyTranscriptBtn.innerHTML;
    copyTranscriptBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
    setTimeout(() => copyTranscriptBtn.innerHTML = originalText, 2000);
  });

  // Export TXT / JSON
  exportTxtBtn.addEventListener('click', () => {
    if (!activeTranscriptData) return;
    const blob = new Blob([`TITLE: ${activeTranscriptData.title}\n\nSUMMARY:\n${activeTranscriptData.summary}\n\nFULL TRANSCRIPT:\n${activeTranscriptData.transcript}`], { type: 'text/plain' });
    downloadFile(blob, 'meeting_summary.txt');
  });

  exportJsonBtn.addEventListener('click', () => {
    if (!activeTranscriptData) return;
    const blob = new Blob([JSON.stringify(activeTranscriptData, null, 2)], { type: 'application/json' });
    downloadFile(blob, 'meeting_data.json');
  });

  function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── 6. RAG AI Chat Interface ──
  sendChatBtn.addEventListener('click', () => sendChatMessage());
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChatMessage();
  });

  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      chatInput.value = prompt;
      sendChatMessage();
    });
  });

  async function sendChatMessage() {
    const question = chatInput.value.trim();
    if (!question) return;

    appendChatMessage('user', question);
    chatInput.value = '';

    const typingBubble = appendChatMessage('assistant', '<i class="fa-solid fa-circle-notch fa-spin"></i> Searching hybrid BM25 + Vector index...');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Chat query failed');

      typingBubble.querySelector('.message-bubble').innerHTML = formatMarkdownText(data.answer);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (err) {
      typingBubble.querySelector('.message-bubble').innerHTML = `<span style="color:#ef4444;">Error: ${err.message}</span>`;
    }
  }

  function appendChatMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${role}`;
    msgDiv.innerHTML = `<div class="message-bubble">${content}</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
  }

  clearMemoryBtn.addEventListener('click', async () => {
    try {
      await fetch('/api/clear-memory', { method: 'POST' });
      chatMessages.innerHTML = `
        <div class="message message-system">
          <div class="message-bubble">🧹 Conversational chat memory reset. You can ask fresh questions now.</div>
        </div>
      `;
    } catch (err) {
      alert('Failed to clear memory');
    }
  });

  // ── Helpers ──
  function showProgressOverlay(title, subtitle) {
    progressTitle.textContent = title;
    progressSubtitle.textContent = subtitle;
    progressBar.style.width = '60%';
    progressContainer.classList.remove('hidden');
  }

  function hideProgressOverlay() {
    progressBar.style.width = '100%';
    setTimeout(() => {
      progressContainer.classList.add('hidden');
      progressBar.style.width = '0%';
    }, 300);
  }

  function updateStatus(statusClass, text) {
    statusBadge.className = `status-badge ${statusClass}`;
    statusBadge.querySelector('.status-text').textContent = text;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatMarkdownText(txt) {
    return txt
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  // ── Auto-Restore Active Session on Page Load ──
  fetch('/api/session')
    .then(res => res.json())
    .then(data => {
      if (data && data.active) {
        console.log('[Session] Restored active document session:', data.source);
        activeTranscriptData = data;
        renderDashboard(data);
        updateStatus('status-ready', 'Indexed & Ready');
      }
    })
    .catch(err => console.debug('[Session] No active session:', err));
});
