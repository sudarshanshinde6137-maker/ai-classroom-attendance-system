/**
 * VisionAttend - AI Classroom Attendance Studio
 * Frontend Application Engine (Async/WebSocket/REST)
 */

(function () {
  'use strict';

  // Global Application State
  const state = {
    currentTab: 'tab-dashboard',
    meta: {
      subjects: [],
      sessions: ['Morning', 'Afternoon', 'Evening'],
      default_subject: '',
      default_session: 'Morning',
      today: new Date().toISOString().split('T')[0],
      trained_faces: 0
    },
    audioEnabled: true,
    jarvisVoiceEnabled: true,
    audioCtx: null,
    lastVoiceAnnouncedStudentId: null,
    jarvisListening: false,
    jarvisSpeaking: false,
    jarvisHandsFree: false,
    jarvisRecognition: null,
    inProjectionMode: false,
    currentStudentProfileData: null,
    cameraStream: null,
    cameraScanning: false,
    scanIntervalId: null,
    autoScanActive: true,
    lastScannedStudentIds: new Set(),
    activeRecords: [],
    allStudents: [],
    groupPhotoFile: null,
    registrationPhotoBlob: null,
    regCamStream: null
  };

  // DOM Elements Cache
  const dom = {
    // Top Bar & Meta
    globalDate: document.getElementById('global-date'),
    globalSession: document.getElementById('global-session'),
    globalSubject: document.getElementById('global-subject'),
    trainedBadge: document.getElementById('trained-badge'),
    clockDisplay: document.getElementById('clock-display'),
    btnRetrain: document.getElementById('btn-retrain'),
    btnSoundToggle: document.getElementById('btn-sound-toggle'),
    soundIcon: document.getElementById('sound-icon'),
    audioSuccess: document.getElementById('audio-success'),
    toastContainer: document.getElementById('toast-container'),

    // Projection HUD
    btnProjectionMode: document.getElementById('btn-projection-mode'),
    projectionOverlay: document.getElementById('projection-hud-overlay'),
    btnCloseProjection: document.getElementById('btn-close-projection'),
    projWebcamVideo: document.getElementById('proj-webcam-video'),
    projDetectionOverlay: document.getElementById('proj-detection-overlay'),
    projRingCircle: document.getElementById('proj-ring-circle'),
    projRingPct: document.getElementById('proj-ring-pct'),
    projStatTotal: document.getElementById('proj-stat-total'),
    projStatPresent: document.getElementById('proj-stat-present'),
    projStatAbsent: document.getElementById('proj-stat-absent'),
    projVibeScore: document.getElementById('proj-vibe-score'),
    projJarvisSpeech: document.getElementById('proj-jarvis-speech'),
    projDatePill: document.getElementById('proj-date-pill'),
    projSessionPill: document.getElementById('proj-session-pill'),
    projSubjectPill: document.getElementById('proj-subject-pill'),
    projClock: document.getElementById('proj-clock'),
    projAdmissionPopup: document.getElementById('proj-admission-popup'),
    projAdmittedPhoto: document.getElementById('proj-admitted-photo'),
    projAdmittedName: document.getElementById('proj-admitted-name'),
    projAdmittedRoll: document.getElementById('proj-admitted-roll'),
    projAdmittedTime: document.getElementById('proj-admitted-time'),
    projStreamList: document.getElementById('proj-stream-list'),
    projLogCount: document.getElementById('proj-log-count'),
    btnChipHandsFree: document.getElementById('btn-chip-hands-free'),

    // J.A.R.V.I.S. AI Voice Assistant & Command Center
    btnJarvisGlobal: document.getElementById('btn-jarvis-global'),
    jarvisFloatingOrb: document.getElementById('jarvis-floating-orb'),
    orbStatusText: document.getElementById('orb-status-text'),
    jarvisConsoleModal: document.getElementById('jarvis-console-modal'),
    jarvisConsoleClose: document.getElementById('jarvis-console-close'),
    jarvisConsoleStatus: document.getElementById('jarvis-console-status'),
    jarvisReactorCore: document.getElementById('jarvis-reactor-core'),
    jarvisVoiceName: document.getElementById('jarvis-voice-name'),
    jarvisModeLabel: document.getElementById('jarvis-mode-label'),
    jarvisWaveCanvas: document.getElementById('jarvis-wave-canvas'),
    jarvisConsoleSpeech: document.getElementById('jarvis-console-speech'),
    btnJarvisMic: document.getElementById('btn-jarvis-mic'),
    jarvisMicText: document.getElementById('jarvis-mic-text'),
    jarvisTextCmd: document.getElementById('jarvis-text-cmd'),
    btnJarvisSend: document.getElementById('btn-jarvis-send'),
    jarvisLogStream: document.getElementById('jarvis-log-stream'),
    btnClearJarvisLog: document.getElementById('btn-clear-jarvis-log'),
    jarvisStatus: document.getElementById('jarvis-status'),
    jarvisTranscript: document.getElementById('jarvis-transcript'),
    jarvisSpectrum: document.getElementById('jarvis-spectrum'),
    btnJarvisSpeakTest: document.getElementById('btn-jarvis-speak-test'),
    btnJarvisAnnounceSummary: document.getElementById('btn-jarvis-announce-summary'),
    btnJarvisToggleVoice: document.getElementById('btn-jarvis-toggle-voice'),

    // Tabs
    navTabs: document.querySelectorAll('.nav-tab'),
    tabPanes: document.querySelectorAll('.tab-pane'),

    // Dashboard
    statTotal: document.getElementById('stat-total'),
    statPresent: document.getElementById('stat-present'),
    statAbsent: document.getElementById('stat-absent'),
    statRate: document.getElementById('stat-rate'),
    statProgressBar: document.getElementById('stat-progress-bar'),
    dashTableBody: document.getElementById('dash-table-body'),
    dashSearch: document.getElementById('dash-search'),
    dashSessionSub: document.getElementById('dash-session-sub'),
    btnDashRefresh: document.getElementById('btn-dash-refresh'),
    subjectBreakdownList: document.getElementById('subject-breakdown-list'),

    // Camera
    videoWrapper: document.getElementById('video-wrapper'),
    webcamVideo: document.getElementById('webcam-video'),
    detectionOverlay: document.getElementById('detection-overlay'),
    camOffline: document.getElementById('cam-offline'),
    camFeedback: document.getElementById('cam-feedback-banner'),
    camTolerance: document.getElementById('cam-tolerance'),
    camToleranceVal: document.getElementById('cam-tolerance-val'),
    btnStartCamera: document.getElementById('btn-start-camera'),
    btnToggleCamera: document.getElementById('btn-toggle-camera'),
    btnAutoScan: document.getElementById('btn-auto-scan'),
    btnManualSnap: document.getElementById('btn-manual-snap'),
    scanSpeedText: document.getElementById('scan-speed-text'),
    sessionMarkedCount: document.getElementById('session-marked-count'),
    liveScansLog: document.getElementById('live-scans-log'),

    // Group Photo
    groupDropzone: document.getElementById('group-dropzone'),
    groupFileInput: document.getElementById('group-file-input'),
    dropzonePrompt: document.getElementById('dropzone-prompt'),
    dropzonePreview: document.getElementById('dropzone-preview'),
    previewImg: document.getElementById('preview-img'),
    btnChangeGroupPhoto: document.getElementById('btn-change-group-photo'),
    groupTolerance: document.getElementById('group-tolerance'),
    groupToleranceVal: document.getElementById('group-tolerance-val'),
    btnProcessGroup: document.getElementById('btn-process-group'),
    annotatedSection: document.getElementById('annotated-result-section'),
    annotatedDisplayImg: document.getElementById('annotated-display-img'),
    groupStatsPills: document.getElementById('group-stats-pills'),
    pillNewly: document.getElementById('pill-newly'),
    pillAlready: document.getElementById('pill-already'),
    pillUnknown: document.getElementById('pill-unknown'),
    groupResultList: document.getElementById('group-result-list'),

    // Register Student
    studentRegForm: document.getElementById('student-reg-form'),
    regName: document.getElementById('reg-name'),
    regRoll: document.getElementById('reg-roll'),
    regPrn: document.getElementById('reg-prn'),
    btnModeFile: document.getElementById('btn-mode-file'),
    btnModeCam: document.getElementById('btn-mode-cam'),
    regFileSection: document.getElementById('reg-file-section'),
    regPhotoFile: document.getElementById('reg-photo-file'),
    regFileLabel: document.getElementById('reg-file-label'),
    regCamSection: document.getElementById('reg-cam-section'),
    regVideo: document.getElementById('reg-video'),
    regCanvas: document.getElementById('reg-canvas'),
    btnRegSnap: document.getElementById('btn-reg-snap'),
    btnRegRetake: document.getElementById('btn-reg-retake'),
    regPreviewBox: document.getElementById('reg-preview-box'),
    regAvatarImg: document.getElementById('reg-avatar-img'),
    previewName: document.getElementById('preview-name'),
    previewRoll: document.getElementById('preview-roll'),
    btnSubmitReg: document.getElementById('btn-submit-reg'),

    // Records
    recFilterDate: document.getElementById('rec-filter-date'),
    recFilterSession: document.getElementById('rec-filter-session'),
    recFilterSubject: document.getElementById('rec-filter-subject'),
    recSearch: document.getElementById('rec-search'),
    btnApplyRecFilters: document.getElementById('btn-apply-rec-filters'),
    recordsTableBody: document.getElementById('records-table-body'),

    // Directory
    dirCountText: document.getElementById('dir-count-text'),
    dirSearch: document.getElementById('dir-search'),
    studentsGrid: document.getElementById('students-grid'),

    // Analytics & Defaulters
    defaulterThresholdSlider: document.getElementById('defaulter-threshold-slider'),
    defaulterThreshLabel: document.getElementById('defaulter-thresh-label'),
    defaulterFilterSubject: document.getElementById('defaulter-filter-subject'),
    defaulterSearchInput: document.getElementById('defaulter-search-input'),
    btnRefreshDefaulters: document.getElementById('btn-refresh-defaulters'),
    defaultersTableBody: document.getElementById('defaulters-table-body'),

    // Monthly Matrix
    matrixMonth: document.getElementById('matrix-month'),
    matrixYear: document.getElementById('matrix-year'),
    matrixSubject: document.getElementById('matrix-subject'),
    btnLoadMatrix: document.getElementById('btn-load-matrix'),
    matrixWrapper: document.getElementById('matrix-wrapper'),

    // Student Portal
    portalQuery: document.getElementById('portal-query'),
    portalResultCard: document.getElementById('portal-result-card')
  };

  /* ==========================================================================
     Toast Notifications
     ========================================================================== */
  function showToast(message, type = 'info', duration = 3500) {
    if (!dom.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  function playSuccessChime() {
    if (!state.audioEnabled) return;
    try {
      if (dom.audioSuccess) {
        dom.audioSuccess.currentTime = 0;
        dom.audioSuccess.play().catch(() => {});
      }
    } catch (e) {
      // Audio playback blocked or unavailable
    }
  }

  /* ==========================================================================
     Tab Navigation
     ========================================================================== */
  window.switchTab = function (tabId) {
    state.currentTab = tabId;
    dom.navTabs.forEach(tab => {
      if (tab.dataset.tab === tabId) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });

    dom.tabPanes.forEach(pane => {
      if (pane.id === tabId) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });

    // Lifecycle triggers
    if (tabId === 'tab-dashboard') {
      loadDashboard();
    } else if (tabId === 'tab-records') {
      loadRecords();
    } else if (tabId === 'tab-students') {
      loadStudents();
    } else if (tabId === 'tab-camera') {
      resizeOverlayCanvas();
    } else if (tabId === 'tab-analytics') {
      loadAnalytics();
    } else if (tabId === 'tab-matrix') {
      loadMonthlyMatrix();
    }
  };

  /* ==========================================================================
     Clock & Meta Init
     ========================================================================== */
  function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour12: false });
    if (dom.clockDisplay) {
      dom.clockDisplay.textContent = timeStr;
    }
    if (dom.projClock) {
      dom.projClock.textContent = timeStr;
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  async function fetchMeta() {
    try {
      const res = await fetch('/api/meta');
      if (!res.ok) throw new Error('Failed to load system metadata');
      const data = await res.json();
      state.meta = data;

      // Populate Global Controls
      if (dom.globalDate) dom.globalDate.value = data.today;
      if (dom.recFilterDate) dom.recFilterDate.value = data.today;

      // Populate Subjects dropdowns
      const populateSelect = (selectElem, items, defaultVal, addAll = false) => {
        if (!selectElem) return;
        selectElem.innerHTML = '';
        if (addAll) {
          const opt = document.createElement('option');
          opt.value = 'All';
          opt.textContent = 'All Subjects';
          selectElem.appendChild(opt);
        }
        items.forEach(item => {
          const opt = document.createElement('option');
          opt.value = item;
          opt.textContent = item;
          if (item === defaultVal) opt.selected = true;
          selectElem.appendChild(opt);
        });
      };

      populateSelect(dom.globalSubject, data.subjects, data.default_subject);
      populateSelect(dom.recFilterSubject, data.subjects, 'All', true);
      populateSelect(dom.defaulterFilterSubject, data.subjects, 'All', true);
      populateSelect(dom.matrixSubject, data.subjects, 'All', true);

      const curDate = new Date();
      if (dom.matrixMonth) dom.matrixMonth.value = String(curDate.getMonth() + 1);
      if (dom.matrixYear) dom.matrixYear.value = String(curDate.getFullYear());

      if (dom.trainedBadge) {
        dom.trainedBadge.textContent = `${data.trained_faces} Enrolled`;
      }

      loadDashboard();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  /* ==========================================================================
     Dashboard
     ========================================================================== */
  async function loadDashboard() {
    const date = dom.globalDate ? dom.globalDate.value : state.meta.today;
    const session = dom.globalSession ? dom.globalSession.value : 'Morning';
    const subject = dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject;

    if (dom.dashSessionSub) {
      dom.dashSessionSub.textContent = `${session} Session • ${subject}`;
    }

    try {
      const url = `/api/dashboard?date=${encodeURIComponent(date)}&session=${encodeURIComponent(session)}&subject=${encodeURIComponent(subject)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch dashboard stats');
      const data = await res.json();

      // Stats
      if (dom.statTotal) dom.statTotal.textContent = data.summary.total;
      if (dom.statPresent) dom.statPresent.textContent = data.summary.present;
      if (dom.statAbsent) dom.statAbsent.textContent = data.summary.absent;
      if (dom.statRate) dom.statRate.textContent = `${data.summary.percentage}%`;
      if (dom.statProgressBar) dom.statProgressBar.style.width = `${data.summary.percentage}%`;

      if (dom.trainedBadge) {
        dom.trainedBadge.textContent = `${data.trained_faces} Enrolled`;
      }

      // Render Subject Breakdown
      if (dom.subjectBreakdownList && data.subject_summary) {
        dom.subjectBreakdownList.innerHTML = '';
        data.subject_summary.forEach(item => {
          const wrapper = document.createElement('div');
          wrapper.className = 'subject-item';
          wrapper.innerHTML = `
            <div class="subj-header">
              <span class="subj-name">${item.subject}</span>
              <span class="subj-stats">${item.present} / ${item.total} (${item.percentage}%)</span>
            </div>
            <div class="subj-bar">
              <div class="subj-bar-fill" style="width: ${item.percentage}%"></div>
            </div>
          `;
          dom.subjectBreakdownList.appendChild(wrapper);
        });
      }

      // Render Attendance Table
      renderDashTable(data.students || []);

    } catch (err) {
      if (dom.dashTableBody) {
        dom.dashTableBody.innerHTML = `<tr><td colspan="6" class="loading-cell text-error">${err.message}</td></tr>`;
      }
    }
  }

  function renderDashTable(students) {
    if (!dom.dashTableBody) return;
    const search = dom.dashSearch ? dom.dashSearch.value.trim().toLowerCase() : '';
    
    const filtered = students.filter(s => {
      if (!search) return true;
      return (
        s.name.toLowerCase().includes(search) ||
        s.roll_no.toLowerCase().includes(search) ||
        s.prn.toLowerCase().includes(search)
      );
    });

    if (filtered.length === 0) {
      dom.dashTableBody.innerHTML = `<tr><td colspan="6" class="loading-cell">No students match current filter.</td></tr>`;
      return;
    }

    dom.dashTableBody.innerHTML = '';
    filtered.forEach(student => {
      const isPresent = student.status === 'Present';
      const tr = document.createElement('tr');

      const avatarHtml = student.photo_url
        ? `<img src="${student.photo_url}" class="student-cell-avatar" alt="${student.name}" onerror="this.onerror=null;this.innerText='👤';">`
        : `<div class="student-cell-avatar">👤</div>`;

      tr.innerHTML = `
        <td>
          <div class="student-cell">
            ${avatarHtml}
            <div>
              <strong>${student.name}</strong>
            </div>
          </div>
        </td>
        <td><code>${student.roll_no}</code></td>
        <td><code>${student.prn}</code></td>
        <td>${student.time || '--'}</td>
        <td>
          <span class="status-pill ${isPresent ? 'status-present' : 'status-absent'}">
            <span class="status-dot"></span>
            ${student.status}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="toggleManualAttendance(${student.id}, '${isPresent ? 'Absent' : 'Present'}')">
            Mark ${isPresent ? 'Absent' : 'Present'}
          </button>
        </td>
      `;
      dom.dashTableBody.appendChild(tr);
    });
  }

  window.toggleManualAttendance = async function (studentId, newStatus) {
    const date = dom.globalDate ? dom.globalDate.value : state.meta.today;
    const session = dom.globalSession ? dom.globalSession.value : 'Morning';
    const subject = dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject;

    try {
      const res = await fetch('/api/attendance/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          date: date,
          session: session,
          subject: subject,
          status: newStatus
        })
      });
      if (!res.ok) throw new Error('Failed to update attendance');
      showToast(`Student attendance updated to ${newStatus}`, 'success', 2000);
      loadDashboard();
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  /* ==========================================================================
     Live Camera Attendance Scanner
     ========================================================================== */
  async function startWebcam() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
      });
      state.cameraStream = stream;
      if (dom.webcamVideo) {
        dom.webcamVideo.srcObject = stream;
        await dom.webcamVideo.play();
      }
      if (dom.camOffline) dom.camOffline.classList.add('hidden');
      if (dom.videoWrapper) dom.videoWrapper.classList.add('scanning-active');
      state.cameraScanning = true;
      resizeOverlayCanvas();
      startAutoScanLoop();
      showToast('Live camera activated', 'success');
      jarvisSpeak('J.A.R.V.I.S. Biometric Vision Engine online. Ready to scan.');
    } catch (err) {
      showToast(`Camera error: ${err.message}`, 'error');
    }
  }

  function stopWebcam() {
    if (state.cameraStream) {
      state.cameraStream.getTracks().forEach(track => track.stop());
      state.cameraStream = null;
    }
    if (state.scanIntervalId) {
      clearInterval(state.scanIntervalId);
      state.scanIntervalId = null;
    }
    state.cameraScanning = false;
    if (dom.camOffline) dom.camOffline.classList.remove('hidden');
    if (dom.videoWrapper) dom.videoWrapper.classList.remove('scanning-active');
    clearOverlayCanvas();
    if (dom.scanSpeedText) dom.scanSpeedText.textContent = 'Camera Off';
    jarvisSpeak('Camera stream deactivated.');
  }

  function resizeOverlayCanvas() {
    if (dom.detectionOverlay && dom.webcamVideo) {
      dom.detectionOverlay.width = dom.webcamVideo.clientWidth;
      dom.detectionOverlay.height = dom.webcamVideo.clientHeight;
    }
    if (dom.projDetectionOverlay && dom.projWebcamVideo) {
      dom.projDetectionOverlay.width = dom.projWebcamVideo.clientWidth;
      dom.projDetectionOverlay.height = dom.projWebcamVideo.clientHeight;
    }
  }
  window.addEventListener('resize', resizeOverlayCanvas);

  function clearOverlayCanvas() {
    if (dom.detectionOverlay) {
      const ctx = dom.detectionOverlay.getContext('2d');
      ctx.clearRect(0, 0, dom.detectionOverlay.width, dom.detectionOverlay.height);
    }
    if (dom.projDetectionOverlay) {
      const ctx = dom.projDetectionOverlay.getContext('2d');
      ctx.clearRect(0, 0, dom.projDetectionOverlay.width, dom.projDetectionOverlay.height);
    }
  }

  function startAutoScanLoop() {
    if (state.scanIntervalId) clearInterval(state.scanIntervalId);
    state.scanIntervalId = setInterval(() => {
      if (state.cameraScanning && state.autoScanActive) {
        captureAndRecognizeFrame();
      }
    }, 1500);
  }

  async function captureAndRecognizeFrame() {
    if (!dom.webcamVideo || dom.webcamVideo.videoWidth === 0) return;

    const startTime = performance.now();
    const snapCanvas = document.createElement('canvas');
    snapCanvas.width = dom.webcamVideo.videoWidth;
    snapCanvas.height = dom.webcamVideo.videoHeight;
    const snapCtx = snapCanvas.getContext('2d');
    snapCtx.drawImage(dom.webcamVideo, 0, 0, snapCanvas.width, snapCanvas.height);

    const b64 = snapCanvas.toDataURL('image/jpeg', 0.82);
    const session = dom.globalSession ? dom.globalSession.value : 'Morning';
    const subject = dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject;
    const tolerance = dom.camTolerance ? parseFloat(dom.camTolerance.value) / 100 : 0.55;

    try {
      const res = await fetch('/api/attendance/scan-frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: b64,
          session: session,
          subject: subject,
          tolerance: tolerance
        })
      });

      if (!res.ok) return;
      const data = await res.json();
      const elapsed = Math.round(performance.now() - startTime);

      if (dom.scanSpeedText) {
        dom.scanSpeedText.textContent = `${elapsed}ms • ${data.faces_detected} face(s)`;
      }

      // Draw bounding boxes on canvas
      drawDetections(data.results || [], snapCanvas.width, snapCanvas.height);

      // Process and log matches
      if (data.results && data.results.length > 0) {
        data.results.forEach(student => {
          if (student.recognized && student.student_id) {
            handleRecognizedStudent(student);
          }
        });
      }
    } catch (e) {
      // Background scan error ignored
    }
  }

  function drawDetections(results, naturalWidth, naturalHeight) {
    if (!dom.detectionOverlay) return;
    const ctx = dom.detectionOverlay.getContext('2d');
    const width = dom.detectionOverlay.width;
    const height = dom.detectionOverlay.height;
    ctx.clearRect(0, 0, width, height);

    if (!results || results.length === 0) return;

    const scaleX = width / naturalWidth;
    const scaleY = height / naturalHeight;

    results.forEach(res => {
      if (!res.location) return;
      let [top, right, bottom, left] = res.location;

      // Note: Video is mirrored via CSS scaleX(-1)
      const boxW = Math.max(20, (right - left) * scaleX);
      const boxH = Math.max(20, (bottom - top) * scaleY);
      const boxX = (naturalWidth - right) * scaleX;
      const boxY = top * scaleY;

      const isKnown = res.recognized;
      let colorPrimary = isKnown ? '#10b981' : '#06b6d4';
      let colorGlow = isKnown ? 'rgba(16, 185, 129, 0.5)' : 'rgba(6, 182, 212, 0.5)';
      let labelTitle = isKnown ? res.name : 'Unknown Subject';
      let labelSub = isKnown ? (res.roll_no ? `Roll: ${res.roll_no}` : 'Verified') : 'No Profile Match';
      let confText = `${Math.round((res.confidence || 0.95) * 100)}%`;

      if (res.spoof_detected) {
        colorPrimary = '#f43f5e';
        colorGlow = 'rgba(244, 63, 94, 0.6)';
        labelTitle = 'SPOOF REJECTED';
        labelSub = 'Photo/Screen Detected';
        confText = '0%';
      }

      ctx.save();

      // 1. Holographic Box Border with Glow
      ctx.shadowColor = colorGlow;
      ctx.shadowBlur = 10;
      ctx.strokeStyle = colorPrimary;
      ctx.lineWidth = 2;
      ctx.strokeRect(boxX, boxY, boxW, boxH);

      // 2. Corner Target Brackets (Cyber HUD style)
      const cLen = Math.min(22, boxW * 0.25, boxH * 0.25);
      ctx.lineWidth = 3.5;
      ctx.strokeStyle = colorPrimary;
      ctx.shadowBlur = 14;

      // Top-Left
      ctx.beginPath();
      ctx.moveTo(boxX, boxY + cLen);
      ctx.lineTo(boxX, boxY);
      ctx.lineTo(boxX + cLen, boxY);
      ctx.stroke();

      // Top-Right
      ctx.beginPath();
      ctx.moveTo(boxX + boxW - cLen, boxY);
      ctx.lineTo(boxX + boxW, boxY);
      ctx.lineTo(boxX + boxW, boxY + cLen);
      ctx.stroke();

      // Bottom-Left
      ctx.beginPath();
      ctx.moveTo(boxX, boxY + boxH - cLen);
      ctx.lineTo(boxX, boxY + boxH);
      ctx.lineTo(boxX + cLen, boxY + boxH);
      ctx.stroke();

      // Bottom-Right
      ctx.beginPath();
      ctx.moveTo(boxX + boxW - cLen, boxY + boxH);
      ctx.lineTo(boxX + boxW, boxY + boxH);
      ctx.lineTo(boxX + boxW, boxY + boxH - cLen);
      ctx.stroke();

      // 3. Center Crosshair Reticle
      ctx.shadowBlur = 0;
      ctx.lineWidth = 1;
      ctx.strokeStyle = colorGlow;
      const midX = boxX + boxW / 2;
      const midY = boxY + boxH / 2;
      ctx.beginPath();
      ctx.moveTo(midX - 7, midY);
      ctx.lineTo(midX + 7, midY);
      ctx.moveTo(midX, midY - 7);
      ctx.lineTo(midX, midY + 7);
      ctx.stroke();

      // 4. Futuristic HUD Header Capsule
      ctx.font = 'bold 12px "Outfit", "Plus Jakarta Sans", sans-serif';
      const titleWidth = ctx.measureText(labelTitle).width;
      ctx.font = '10px "JetBrains Mono", monospace';
      const subWidth = ctx.measureText(labelSub).width;
      const confWidth = ctx.measureText(confText).width;

      const badgeW = Math.max(titleWidth, subWidth) + confWidth + 34;
      const badgeH = 34;
      const badgeX = Math.max(4, Math.min(boxX, width - badgeW - 4));
      const badgeY = Math.max(badgeH + 4, boxY - 8);

      // Glass pill background
      ctx.shadowColor = 'rgba(0,0,0,0.6)';
      ctx.shadowBlur = 10;
      ctx.fillStyle = 'rgba(7, 11, 22, 0.9)';
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(badgeX, badgeY - badgeH, badgeW, badgeH, 6);
      } else {
        ctx.rect(badgeX, badgeY - badgeH, badgeW, badgeH);
      }
      ctx.fill();

      // Colored Left Accent Bar
      ctx.fillStyle = colorPrimary;
      ctx.fillRect(badgeX, badgeY - badgeH, 4, badgeH);

      // Text Title
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 12px "Outfit", "Plus Jakarta Sans", sans-serif';
      ctx.fillText(labelTitle, badgeX + 12, badgeY - 18);

      // Text Subtitle (Roll / Status)
      ctx.fillStyle = '#94A3B8';
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillText(labelSub, badgeX + 12, badgeY - 6);

      // Confidence Pill on Right
      const pillW = confWidth + 12;
      const pillX = badgeX + badgeW - pillW - 6;
      const pillY = badgeY - badgeH + 7;
      ctx.fillStyle = colorGlow;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(pillX, pillY, pillW, 20, 10);
      } else {
        ctx.rect(pillX, pillY, pillW, 20);
      }
      ctx.fill();

      ctx.fillStyle = colorPrimary;
      ctx.font = 'bold 10px "JetBrains Mono", monospace';
      ctx.fillText(confText, pillX + 6, pillY + 14);

      ctx.restore();
    });
  }

  /* ==========================================================================
     J.A.R.V.I.S. AI Biometric Voice Engine & Web Audio Synthesizer
     ========================================================================== */
  function getAudioContext() {
    if (!state.audioCtx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) state.audioCtx = new AudioCtx();
    }
    if (state.audioCtx && state.audioCtx.state === 'suspended') {
      state.audioCtx.resume();
    }
    return state.audioCtx;
  }

  function playSciFiChime() {
    if (!state.audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(540, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.32);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.33);
    } catch (e) {
      if (dom.audioSuccess) dom.audioSuccess.play().catch(() => {});
    }
  }

  function playJarvisBootChime() {
    if (!state.audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        const start = ctx.currentTime + idx * 0.06;
        osc.frequency.setValueAtTime(freq, start);
        gain.gain.setValueAtTime(0.18, start);
        gain.gain.exponentialRampToValueAtTime(0.001, start + 0.25);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(start);
        osc.stop(start + 0.26);
      });
    } catch (e) {}
  }

  function playListeningBeep() {
    if (!state.audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(660, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1100, ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.21);
    } catch (e) {}
  }

  function playClickSound() {
    if (!state.audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, ctx.currentTime);
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.05);
    } catch (e) {}
  }

  function appendJarvisLog(sender, text, isUser = false) {
    if (!dom.jarvisLogStream) return;
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    const entry = document.createElement('div');
    entry.className = `jarvis-log-entry ${isUser ? 'user-msg' : 'jarvis-msg'}`;
    entry.innerHTML = `
      <span class="entry-time">${timeStr}</span>
      <span class="entry-sender">${sender}:</span>
      <span class="entry-content">${escapeHtml(text)}</span>
    `;
    dom.jarvisLogStream.appendChild(entry);
    dom.jarvisLogStream.scrollTop = dom.jarvisLogStream.scrollHeight;
  }

  function startOscilloscopeRenderer() {
    if (!dom.jarvisWaveCanvas) return;
    const canvas = dom.jarvisWaveCanvas;
    const ctx = canvas.getContext('2d');
    let phase = 0;

    function render() {
      requestAnimationFrame(render);
      const width = canvas.width = canvas.parentElement ? canvas.parentElement.clientWidth : 480;
      const height = canvas.height = 80;
      ctx.clearRect(0, 0, width, height);

      // Cyber Grid
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.06)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x < width; x += 32) {
        ctx.moveTo(x, 0); ctx.lineTo(x, height);
      }
      ctx.moveTo(0, height / 2); ctx.lineTo(width, height / 2);
      ctx.stroke();

      let amplitude = 7;
      let frequency = 0.024;
      let speed = 0.04;
      let strokeStyle = 'rgba(0, 242, 254, 0.6)';
      let shadowColor = '#00f2fe';

      if (state.jarvisSpeaking) {
        amplitude = 25 + Math.sin(phase * 4) * 8;
        frequency = 0.042;
        speed = 0.12;
        strokeStyle = '#00f2fe';
        shadowColor = '#00f2fe';
      } else if (state.jarvisListening) {
        amplitude = 20 + Math.sin(phase * 3) * 6;
        frequency = 0.035;
        speed = 0.09;
        strokeStyle = '#10b981';
        shadowColor = '#10b981';
      }

      phase += speed;

      // Primary Wave
      ctx.save();
      ctx.strokeStyle = strokeStyle;
      ctx.shadowColor = shadowColor;
      ctx.shadowBlur = (state.jarvisSpeaking || state.jarvisListening) ? 14 : 4;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const y = height / 2 + Math.sin(x * frequency + phase) * amplitude * Math.sin((x / width) * Math.PI);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Secondary Harmonic Wave
      ctx.strokeStyle = state.jarvisListening ? 'rgba(56, 189, 248, 0.45)' : 'rgba(168, 85, 247, 0.55)';
      ctx.lineWidth = 1.5;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const y = height / 2 + Math.cos(x * (frequency * 1.5) - phase * 1.2) * (amplitude * 0.6) * Math.sin((x / width) * Math.PI);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.restore();
    }

    render();
  }

  function jarvisSpeak(text, priority = false) {
    if (!text) return;

    if (dom.jarvisConsoleSpeech) {
      dom.jarvisConsoleSpeech.textContent = `"${text}"`;
    }
    if (dom.jarvisTranscript) {
      dom.jarvisTranscript.textContent = `"${text}"`;
    }

    if (!state.jarvisVoiceEnabled || !('speechSynthesis' in window)) return;

    try {
      if (priority) {
        window.speechSynthesis.cancel();
      } else if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.02;
      utterance.pitch = 0.94;

      const voices = window.speechSynthesis.getVoices();
      const jarvisVoice = voices.find(v => 
        /en-GB|en_GB|British|Daniel|George|Arthur|Oliver|Male/i.test(v.name + ' ' + v.lang)
      ) || voices.find(v => v.lang && v.lang.startsWith('en')) || voices[0];

      if (jarvisVoice) {
        utterance.voice = jarvisVoice;
        if (dom.jarvisVoiceName) {
          dom.jarvisVoiceName.textContent = jarvisVoice.name.substring(0, 14);
        }
      }

      utterance.onstart = () => {
        state.jarvisSpeaking = true;
        if (dom.jarvisSpectrum) dom.jarvisSpectrum.classList.add('speaking');
        if (dom.jarvisFloatingOrb) dom.jarvisFloatingOrb.classList.add('speaking');
        if (dom.orbStatusText) dom.orbStatusText.textContent = 'SPEAKING...';
        if (dom.jarvisModeLabel) dom.jarvisModeLabel.textContent = 'TRANSMITTING';
      };

      utterance.onend = utterance.onerror = () => {
        state.jarvisSpeaking = false;
        if (dom.jarvisSpectrum) dom.jarvisSpectrum.classList.remove('speaking');
        if (dom.jarvisFloatingOrb) dom.jarvisFloatingOrb.classList.remove('speaking');
        if (dom.orbStatusText) dom.orbStatusText.textContent = state.jarvisListening ? 'LISTENING...' : 'JARVIS READY';
        if (dom.jarvisModeLabel) dom.jarvisModeLabel.textContent = state.jarvisListening ? 'LISTENING' : 'STANDBY';
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('JARVIS speech synthesis error:', e);
    }
  }

  function announceAttendanceSummary() {
    playJarvisBootChime();
    const session = (dom.globalSession && dom.globalSession.value) || state.meta.default_session || 'Morning';
    const subject = (dom.globalSubject && dom.globalSubject.value) || state.meta.default_subject || 'General';
    const total = state.allStudents.length;
    const present = state.activeRecords.length;
    const absent = Math.max(0, total - present);
    const rate = total > 0 ? Math.round((present / total) * 100) : 0;

    let briefing = `Attendance briefing for ${subject}, ${session} session. Total roster: ${total} students. Verified present: ${present}. Pending absent: ${absent}. Present rate: ${rate} percent.`;
    if (rate >= 80) {
      briefing += ` Class attendance is in optimal standing.`;
    } else if (rate < 60 && total > 0) {
      briefing += ` Caution: Attendance is below benchmark. Defaulter notices are prepared.`;
    }

    appendJarvisLog('J.A.R.V.I.S.', briefing);
    jarvisSpeak(briefing, true);
  }

  function toggleJarvisVoice() {
    state.jarvisVoiceEnabled = !state.jarvisVoiceEnabled;
    const isEnabled = state.jarvisVoiceEnabled;
    if (dom.btnJarvisToggleVoice) {
      dom.btnJarvisToggleVoice.textContent = isEnabled ? '🔊 Voice: ON' : '🔇 Voice: OFF';
      dom.btnJarvisToggleVoice.className = isEnabled ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
    }
    if (dom.jarvisStatus) {
      dom.jarvisStatus.className = isEnabled ? 'jarvis-status-pill active' : 'jarvis-status-pill muted';
      dom.jarvisStatus.innerHTML = isEnabled ? '<span class="pulse-dot"></span> ONLINE' : '<span class="pulse-dot" style="background:#64748b;"></span> MUTED';
    }
    if (dom.jarvisConsoleStatus) {
      dom.jarvisConsoleStatus.className = isEnabled ? 'jarvis-status-pill active' : 'jarvis-status-pill muted';
      dom.jarvisConsoleStatus.innerHTML = isEnabled ? '<span class="pulse-dot"></span> SYSTEMS NOMINAL' : '<span class="pulse-dot" style="background:#64748b;"></span> VOICE MUTED';
    }

    showToast(isEnabled ? 'J.A.R.V.I.S. voice feedback enabled' : 'J.A.R.V.I.S. voice muted', 'info');
    if (isEnabled) {
      playJarvisBootChime();
      jarvisSpeak('Voice feedback online and operational.', true);
    }
  }

  function testJarvisVoice() {
    playJarvisBootChime();
    jarvisSpeak('J.A.R.V.I.S. biometric neural vision engine calibrated and online. Ready to scan.', true);
  }

  function openJarvisModal() {
    playJarvisBootChime();
    if (dom.jarvisConsoleModal) {
      dom.jarvisConsoleModal.classList.remove('hidden');
    }
    if (dom.jarvisTextCmd) {
      dom.jarvisTextCmd.focus();
    }
  }

  function closeJarvisModal() {
    playClickSound();
    if (dom.jarvisConsoleModal) {
      dom.jarvisConsoleModal.classList.add('hidden');
    }
    if (state.jarvisListening && state.jarvisRecognition) {
      state.jarvisRecognition.stop();
    }
  }

  async function executeJarvisCommand(rawCmd) {
    if (!rawCmd || !rawCmd.trim()) return;
    const cmd = rawCmd.trim();
    appendJarvisLog('USER', cmd, true);

    const lower = cmd.toLowerCase();

    // 1. Briefing / Status
    if (lower.includes('briefing') || lower.includes('status') || lower.includes('report') || lower.includes('summary') || lower.includes('how is attendance')) {
      announceAttendanceSummary();
      return;
    }

    // 2. Who is absent
    if (lower.includes('absent') || lower.includes('missing') || lower.includes("who didn't") || lower.includes('who is not')) {
      const activeSubject = (dom.globalSubject && dom.globalSubject.value) || state.meta.default_subject || 'All Subjects';
      const presentIds = new Set(state.activeRecords.map(r => r.student_id));
      const absentStudents = state.allStudents.filter(s => !presentIds.has(s.id));

      if (absentStudents.length === 0) {
        const msg = `Outstanding attendance! All ${state.allStudents.length} enrolled students are present for ${activeSubject}.`;
        appendJarvisLog('J.A.R.V.I.S.', msg);
        jarvisSpeak(msg, true);
      } else {
        const names = absentStudents.slice(0, 5).map(s => `${s.first_name} ${s.last_name}`).join(', ');
        const remaining = absentStudents.length > 5 ? ` and ${absentStudents.length - 5} more` : '';
        const msg = `Currently, ${absentStudents.length} students are absent for ${activeSubject}: ${names}${remaining}. Total enrolled: ${state.allStudents.length}.`;
        appendJarvisLog('J.A.R.V.I.S.', msg);
        jarvisSpeak(msg, true);
      }
      return;
    }

    // 3. Who is present
    if (lower.includes('present') || lower.includes('verified') || lower.includes('marked')) {
      const activeSubject = (dom.globalSubject && dom.globalSubject.value) || state.meta.default_subject || 'All Subjects';
      if (state.activeRecords.length === 0) {
        const msg = `No students have been marked present yet for ${activeSubject} today. The optical scanner is ready to scan.`;
        appendJarvisLog('J.A.R.V.I.S.', msg);
        jarvisSpeak(msg, true);
      } else {
        const names = state.activeRecords.slice(0, 5).map(r => r.name || r.student_name).join(', ');
        const remaining = state.activeRecords.length > 5 ? ` and ${state.activeRecords.length - 5} more` : '';
        const msg = `${state.activeRecords.length} students verified present: ${names}${remaining}. Attendance logged successfully.`;
        appendJarvisLog('J.A.R.V.I.S.', msg);
        jarvisSpeak(msg, true);
      }
      return;
    }

    // 4. Defaulters audit
    if (lower.includes('defaulter') || lower.includes('below 75') || lower.includes('low attendance') || lower.includes('audit')) {
      window.switchTab('tab-analytics');
      const msg = `Initiating academic defaulters audit. Switching to Defaulter Analysis console.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    // 5. Start camera / scanning
    if (lower.includes('start camera') || lower.includes('scan') || lower.includes('take attendance') || lower.includes('open camera') || lower.includes('deploy scanner')) {
      window.switchTab('tab-camera');
      if (!state.cameraScanning) {
        startWebcam();
      }
      const msg = `Optical scanner deployed. Live face recognition camera active.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    // 6. Stop camera
    if (lower.includes('stop camera') || lower.includes('close camera') || lower.includes('turn off camera')) {
      if (state.cameraScanning) {
        stopWebcam();
      }
      const msg = `Optical camera stream halted. Sensor placed on standby.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    // 7. Tab switches
    if (lower.includes('matrix') || lower.includes('register sheet') || lower.includes('monthly')) {
      window.switchTab('tab-matrix');
      const msg = `Navigating to Monthly Register Matrix sheet.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('directory') || lower.includes('student list') || lower.includes('roster')) {
      window.switchTab('tab-students');
      const msg = `Displaying student directory and enrollment profiles.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('register') || lower.includes('enroll') || lower.includes('new student')) {
      window.switchTab('tab-register');
      const msg = `Switching to Biometric Student Registration console.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('records') || lower.includes('history') || lower.includes('log')) {
      window.switchTab('tab-records');
      const msg = `Accessing attendance records archive.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('group photo') || lower.includes('classroom photo')) {
      window.switchTab('tab-group-photo');
      const msg = `Classroom Group Photo attendance processor ready.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('dashboard') || lower.includes('home')) {
      window.switchTab('tab-dashboard');
      const msg = `Returning to executive command dashboard.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    // 8. Export Excel
    if (lower.includes('export') || lower.includes('download excel') || lower.includes('excel report')) {
      const msg = `Compiling official attendance ledger into formatted Excel workbook.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      const date = (dom.globalDate && dom.globalDate.value) || state.meta.today;
      const session = (dom.globalSession && dom.globalSession.value) || 'Morning';
      const subject = (dom.globalSubject && dom.globalSubject.value) || 'Mathematics';
      window.location.href = `/api/export/excel?date=${encodeURIComponent(date)}&session=${encodeURIComponent(session)}&subject=${encodeURIComponent(subject)}`;
      return;
    }

    // 9. Projection Mode
    if (lower.includes('projection') || lower.includes('smartboard') || lower.includes('theater')) {
      openProjectionMode();
      return;
    }

    // 10. Hands Free
    if (lower.includes('hands free') || lower.includes('hands-free') || lower.includes('wake word')) {
      toggleHandsFreeJarvis();
      return;
    }

    // 11. ID Pass / Badge
    if (lower.includes('id card') || lower.includes('badge') || lower.includes('pass')) {
      if (state.allStudents.length > 0) {
        window.openStudentProfile(state.allStudents[0].id);
        window.switchProfileSubtab('profile-tab-badge');
        const msg = `Displaying holographic student biometric pass.`;
        appendJarvisLog('J.A.R.V.I.S.', msg);
        jarvisSpeak(msg, true);
      }
      return;
    }

    // 12. Voice Toggle
    if (lower.includes('toggle voice') || lower.includes('mute') || lower.includes('unmute') || lower.includes('silence')) {
      toggleJarvisVoice();
      return;
    }

    // 13. Greetings & Personality
    if (lower.includes('hello') || lower.includes('hey jarvis') || lower.includes('hi jarvis') || lower.includes('good morning') || lower.includes('good afternoon')) {
      const msg = `Good day. J.A.R.V.I.S. neural biometric assistant is fully operational. How may I assist your classroom session today?`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('who are you') || lower.includes('what are you')) {
      const msg = `I am J.A.R.V.I.S., an autonomous AI assistant powering this biometric facial recognition attendance studio. I manage camera streams, student rosters, academic defaulters, and automated ledger exports.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    if (lower.includes('help') || lower.includes('command') || lower.includes('what can you do')) {
      const msg = `You can speak or type commands like: "Who is absent?", "Briefing report", "Audit defaulters", "Start camera", "Projection mode", "Hands free", or "Export excel".`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    // Check student query
    const foundStudent = state.allStudents.find(s => {
      const fullName = `${s.first_name} ${s.last_name}`.toLowerCase();
      return lower.includes(fullName) || lower.includes(s.first_name.toLowerCase()) || (s.roll_no && lower.includes(s.roll_no.toLowerCase()));
    });

    if (foundStudent) {
      const isPresent = state.activeRecords.some(r => r.student_id === foundStudent.id);
      const statusText = isPresent ? 'verified present today' : 'currently absent for today\'s session';
      const msg = `Student profile found: ${foundStudent.first_name} ${foundStudent.last_name} (Roll: ${foundStudent.roll_no || 'N/A'}). Status: ${statusText}.`;
      appendJarvisLog('J.A.R.V.I.S.', msg);
      jarvisSpeak(msg, true);
      return;
    }

    const msg = `Command acknowledged: "${cmd}". No direct routine mapped. Try asking: "Who is absent?", "Briefing report", "Projection mode", or "Start camera".`;
    appendJarvisLog('J.A.R.V.I.S.', msg);
    jarvisSpeak(msg, true);
  }

  function toggleHandsFreeJarvis() {
    state.jarvisHandsFree = !state.jarvisHandsFree;
    const isHandsFree = state.jarvisHandsFree;
    const btn = document.getElementById('btn-chip-hands-free');
    if (btn) {
      btn.textContent = isHandsFree ? '🎙️ Hands-Free: ON' : '🎙️ Hands-Free: OFF';
      btn.style.borderColor = isHandsFree ? '#10b981' : '';
      btn.style.color = isHandsFree ? '#10b981' : '';
    }
    if (isHandsFree) {
      playListeningBeep();
      showToast('Hands-Free "Hey Jarvis" Mode Activated! Say "Hey Jarvis" followed by your command.', 'success', 3500);
      jarvisSpeak('Hands-free audio trigger active. Say "Hey Jarvis" whenever you need assistance.', true);
      if (state.jarvisRecognition) {
        try { state.jarvisRecognition.start(); } catch (e) {}
      }
    } else {
      showToast('Hands-Free Mode Deactivated.', 'info', 2000);
      if (state.jarvisRecognition && state.jarvisListening) {
        state.jarvisRecognition.stop();
      }
    }
  }

  function setupSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (dom.btnJarvisMic) {
        dom.btnJarvisMic.title = 'Speech recognition not supported in this browser. Please use text input.';
        dom.btnJarvisMic.addEventListener('click', () => {
          showToast('Speech recognition not supported in this browser. Please use the text input below.', 'info');
        });
      }
      return;
    }

    const recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      state.jarvisListening = true;
      if (dom.btnJarvisMic) {
        dom.btnJarvisMic.classList.add('listening');
        if (dom.jarvisMicText) dom.jarvisMicText.textContent = 'Listening... Speak now';
      }
      if (dom.jarvisFloatingOrb) dom.jarvisFloatingOrb.classList.add('listening');
      if (dom.orbStatusText) dom.orbStatusText.textContent = 'LISTENING...';
      if (dom.jarvisModeLabel) dom.jarvisModeLabel.textContent = 'LISTENING';
      if (dom.jarvisConsoleStatus) {
        dom.jarvisConsoleStatus.innerHTML = '<span class="pulse-dot" style="background:#10b981;"></span> LISTENING...';
      }
    };

    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      if (dom.jarvisTextCmd) dom.jarvisTextCmd.value = transcript;

      const lower = transcript.toLowerCase();
      if (state.jarvisHandsFree) {
        if (lower.startsWith('hey jarvis') || lower.startsWith('jarvis') || lower.startsWith('okay jarvis')) {
          playListeningBeep();
          const cleanCmd = transcript.replace(/^(hey jarvis|jarvis|okay jarvis)\s*,?\s*/i, '');
          if (cleanCmd) {
            executeJarvisCommand(cleanCmd);
          } else {
            jarvisSpeak('Yes, Professor? How may I assist you?', true);
          }
        } else {
          executeJarvisCommand(transcript);
        }
      } else {
        executeJarvisCommand(transcript);
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
    };

    recognition.onend = () => {
      state.jarvisListening = false;
      if (dom.btnJarvisMic) {
        dom.btnJarvisMic.classList.remove('listening');
        if (dom.jarvisMicText) dom.jarvisMicText.textContent = 'Speak to JARVIS';
      }
      if (dom.jarvisFloatingOrb) dom.jarvisFloatingOrb.classList.remove('listening');
      if (dom.orbStatusText) dom.orbStatusText.textContent = state.jarvisHandsFree ? 'HANDS-FREE ON' : 'JARVIS READY';
      if (dom.jarvisModeLabel) dom.jarvisModeLabel.textContent = 'STANDBY';
      if (dom.jarvisConsoleStatus) {
        dom.jarvisConsoleStatus.innerHTML = '<span class="pulse-dot"></span> SYSTEMS NOMINAL';
      }

      if (state.jarvisHandsFree && !state.jarvisSpeaking) {
        setTimeout(() => {
          if (state.jarvisHandsFree && !state.jarvisSpeaking && !state.jarvisListening) {
            try { recognition.start(); } catch (e) {}
          }
        }, 500);
      }
    };

    state.jarvisRecognition = recognition;

    if (dom.btnJarvisMic) {
      dom.btnJarvisMic.addEventListener('click', () => {
        playListeningBeep();
        if (state.jarvisListening) {
          recognition.stop();
        } else {
          try {
            recognition.start();
          } catch (e) {
            recognition.stop();
          }
        }
      });
    }
  }

  /* ==========================================================================
     Lecture Hall Projection Mode (Smartboard Theater Display)
     ========================================================================== */
  function openProjectionMode() {
    state.inProjectionMode = true;
    if (dom.projectionOverlay) {
      dom.projectionOverlay.classList.remove('hidden');
    }

    if (dom.projWebcamVideo && state.cameraStream) {
      dom.projWebcamVideo.srcObject = state.cameraStream;
      dom.projWebcamVideo.play().catch(() => {});
    } else {
      startWebcam().then(() => {
        if (dom.projWebcamVideo && state.cameraStream) {
          dom.projWebcamVideo.srcObject = state.cameraStream;
          dom.projWebcamVideo.play().catch(() => {});
        }
      });
    }

    updateProjectionStats();
    playJarvisBootChime();
    jarvisSpeak("Lecture Hall Projection HUD online. Initializing smartboard display.", true);

    if (dom.projDatePill) dom.projDatePill.textContent = (dom.globalDate && dom.globalDate.value) || state.meta.today;
    if (dom.projSessionPill) dom.projSessionPill.textContent = (dom.globalSession && dom.globalSession.value) || 'Morning';
    if (dom.projSubjectPill) dom.projSubjectPill.textContent = (dom.globalSubject && dom.globalSubject.value) || 'General';
  }

  function closeProjectionMode() {
    state.inProjectionMode = false;
    if (dom.projectionOverlay) {
      dom.projectionOverlay.classList.add('hidden');
    }
    playClickSound();
  }

  function updateProjectionStats() {
    const total = state.allStudents.length;
    const present = state.activeRecords.length;
    const absent = Math.max(0, total - present);
    const pct = total > 0 ? Math.round((present / total) * 100) : 0;

    if (dom.projStatTotal) dom.projStatTotal.textContent = total;
    if (dom.projStatPresent) dom.projStatPresent.textContent = present;
    if (dom.projStatAbsent) dom.projStatAbsent.textContent = absent;
    if (dom.projRingPct) dom.projRingPct.textContent = `${pct}%`;

    if (dom.projRingCircle) {
      const offset = 427 - (427 * (pct / 100));
      dom.projRingCircle.style.strokeDashoffset = offset;
    }
    if (dom.projLogCount) {
      dom.projLogCount.textContent = `${present} Verified`;
    }
  }

  function showProjectionAdmissionPopup(student) {
    if (!dom.projAdmissionPopup) return;
    if (dom.projAdmittedPhoto) {
      dom.projAdmittedPhoto.src = student.photo_url || '';
    }
    if (dom.projAdmittedName) {
      dom.projAdmittedName.textContent = student.name;
    }
    if (dom.projAdmittedRoll) {
      dom.projAdmittedRoll.textContent = student.roll_no ? `Roll: ${student.roll_no}` : 'Verified';
    }
    if (dom.projAdmittedTime) {
      dom.projAdmittedTime.textContent = new Date().toTimeString().split(' ')[0];
    }
    dom.projAdmissionPopup.classList.remove('hidden');

    if (dom.projStreamList) {
      const emptyHint = dom.projStreamList.querySelector('.proj-empty-stream');
      if (emptyHint) emptyHint.remove();

      const item = document.createElement('div');
      item.className = 'proj-log-item';
      const photoSrc = student.photo_url || '';
      item.innerHTML = `
        ${photoSrc ? `<img src="${photoSrc}" alt="${escapeHtml(student.name)}">` : '<div style="width:36px;height:36px;border-radius:50%;background:#0284c7;display:flex;align-items:center;justify-content:center;font-size:16px;">👤</div>'}
        <div class="proj-log-meta">
          <span class="proj-log-name">${escapeHtml(student.name)}</span>
          <span class="proj-log-sub">Roll: ${student.roll_no || '--'} • Confidence: ${Math.round((student.confidence || 0.95) * 100)}%</span>
        </div>
        <div class="proj-log-time">${new Date().toTimeString().split(' ')[0]}</div>
      `;
      dom.projStreamList.prepend(item);
    }

    setTimeout(() => {
      if (dom.projAdmissionPopup) {
        dom.projAdmissionPopup.classList.add('hidden');
      }
    }, 3800);
  }

  /* ==========================================================================
     Cyber Holographic Student ID Pass Generator
     ========================================================================== */
  function drawCyberQrCode(text) {
    const canvas = document.getElementById('id-qr-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = canvas.width;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);

    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = ((hash << 5) - hash) + text.charCodeAt(i);
      hash |= 0;
    }

    const gridSize = 21;
    const cellSize = size / gridSize;
    ctx.fillStyle = '#030712';

    function drawFinder(startX, startY) {
      for (let r = 0; r < 7; r++) {
        for (let c = 0; c < 7; c++) {
          if (r === 0 || r === 6 || c === 0 || c === 6 || (r >= 2 && r <= 4 && c >= 2 && c <= 4)) {
            ctx.fillRect((startX + c) * cellSize, (startY + r) * cellSize, cellSize, cellSize);
          }
        }
      }
    }

    drawFinder(0, 0);
    drawFinder(gridSize - 7, 0);
    drawFinder(0, gridSize - 7);

    for (let r = 0; r < gridSize; r++) {
      for (let c = 0; c < gridSize; c++) {
        if ((r < 8 && c < 8) || (r < 8 && c >= gridSize - 8) || (r >= gridSize - 8 && c < 8)) {
          continue;
        }
        if (r === 6 || c === 6) {
          if ((r + c) % 2 === 0) {
            ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
          }
          continue;
        }
        const val = Math.sin(hash + r * 17 + c * 31);
        if (val > 0.08) {
          ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
        }
      }
    }
  }

  function setupCyberCardTilt() {
    const card = document.getElementById('cyber-id-card');
    if (!card) return;
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const rotX = -(y / (rect.height / 2)) * 12;
      const rotY = (x / (rect.width / 2)) * 12;
      card.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.02)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'rotateX(0deg) rotateY(0deg) scale(1)';
    });
  }

  window.printCyberIdCard = function () {
    window.print();
  };

  window.downloadCyberIdCard = function () {
    showToast('Digital ID card verified! Ready for printing or presentation.', 'success', 2500);
    window.print();
  };

  function handleRecognizedStudent(student) {
    if (student.spoof_detected) {
      playAlertWarningSound();
      flashFeedbackBanner(`⚠️ Spoof Rejected: ${student.name}`);
      showToast(`Liveness check failed for ${student.name} (Screen or Photo Detected)`, 'error', 3000);
      jarvisSpeak(`Warning: Liveness verification rejected for ${student.name || 'unauthorized subject'}.`, true);
      return;
    }

    const isNew = student.marked_now;
    if (isNew) {
      playSciFiChime();
      flashFeedbackBanner(`Marked Present: ${student.name}`);
      jarvisSpeak(`Welcome, ${student.name}. Attendance logged.`);
      loadDashboard(); // Refresh stats
    } else if (state.lastVoiceAnnouncedStudentId !== student.student_id) {
      state.lastVoiceAnnouncedStudentId = student.student_id;
      playSciFiChime();
      jarvisSpeak(`Identity verified: ${student.name}. Already recorded.`);
    }

    // Trigger Projection HUD admission popup if open
    if (state.inProjectionMode) {
      showProjectionAdmissionPopup(student);
      updateProjectionStats();
      if (dom.projJarvisSpeech) {
        dom.projJarvisSpeech.textContent = `"${student.name} verified and admitted. Class attendance updated."`;
      }
    }

    // Add to Live Stream Log if not flooded
    appendLiveScanLog(student, isNew);
  }

  function flashFeedbackBanner(msg) {
    if (!dom.camFeedback) return;
    dom.camFeedback.textContent = msg;
    dom.camFeedback.classList.remove('hidden');
    setTimeout(() => {
      dom.camFeedback.classList.add('hidden');
    }, 2800);
  }

  function appendLiveScanLog(student, isNew) {
    if (!dom.liveScansLog) return;
    const emptyHint = dom.liveScansLog.querySelector('.empty-log-hint');
    if (emptyHint) emptyHint.remove();

    state.lastScannedStudentIds.add(student.student_id);
    if (dom.sessionMarkedCount) {
      dom.sessionMarkedCount.textContent = `${state.lastScannedStudentIds.size} Marked`;
    }

    const item = document.createElement('div');
    item.className = 'scan-log-item';
    const tagClass = isNew ? 'tag-new' : 'tag-repeat';
    const tagText = isNew ? 'Just Marked' : 'Verified';

    item.innerHTML = `
      <div class="scan-avatar">${student.name.charAt(0)}</div>
      <div class="scan-info">
        <div class="scan-name">${student.name}</div>
        <div class="scan-meta">
          <span>${student.roll_no}</span>
          <span>•</span>
          <span>${new Date().toLocaleTimeString([], { hour12: false })}</span>
        </div>
      </div>
      <div class="scan-tag ${tagClass}">${tagText}</div>
    `;

    dom.liveScansLog.insertBefore(item, dom.liveScansLog.firstChild);
    // Keep max 15 entries
    while (dom.liveScansLog.children.length > 15) {
      dom.liveScansLog.removeChild(dom.liveScansLog.lastChild);
    }
  }

  /* ==========================================================================
     Group Photo Attendance
     ========================================================================== */
  function setupGroupPhoto() {
    if (!dom.groupDropzone || !dom.groupFileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      dom.groupDropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dom.groupDropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dom.groupDropzone.addEventListener(eventName, e => {
        e.preventDefault();
        dom.groupDropzone.classList.remove('dragover');
      });
    });

    dom.groupDropzone.addEventListener('drop', e => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files[0]) {
        handleSelectedGroupFile(dt.files[0]);
      }
    });

    dom.groupFileInput.addEventListener('change', () => {
      if (dom.groupFileInput.files && dom.groupFileInput.files[0]) {
        handleSelectedGroupFile(dom.groupFileInput.files[0]);
      }
    });

    if (dom.btnChangeGroupPhoto) {
      dom.btnChangeGroupPhoto.addEventListener('click', (e) => {
        e.stopPropagation();
        resetGroupPhotoUI();
      });
    }

    if (dom.groupTolerance) {
      dom.groupTolerance.addEventListener('input', () => {
        if (dom.groupToleranceVal) {
          dom.groupToleranceVal.textContent = `${dom.groupTolerance.value}%`;
        }
      });
    }

    if (dom.btnProcessGroup) {
      dom.btnProcessGroup.addEventListener('click', processGroupPhoto);
    }
  }

  function handleSelectedGroupFile(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Please select a valid image file', 'error');
      return;
    }
    state.groupPhotoFile = file;

    const reader = new FileReader();
    reader.onload = e => {
      if (dom.previewImg) dom.previewImg.src = e.target.result;
      if (dom.dropzonePrompt) dom.dropzonePrompt.classList.add('hidden');
      if (dom.dropzonePreview) dom.dropzonePreview.classList.remove('hidden');
      if (dom.btnProcessGroup) dom.btnProcessGroup.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function resetGroupPhotoUI() {
    state.groupPhotoFile = null;
    if (dom.groupFileInput) dom.groupFileInput.value = '';
    if (dom.dropzonePrompt) dom.dropzonePrompt.classList.remove('hidden');
    if (dom.dropzonePreview) dom.dropzonePreview.classList.add('hidden');
    if (dom.btnProcessGroup) dom.btnProcessGroup.disabled = true;
    if (dom.annotatedSection) dom.annotatedSection.classList.add('hidden');
    if (dom.groupStatsPills) dom.groupStatsPills.classList.add('hidden');
    if (dom.groupResultList) dom.groupResultList.innerHTML = '<div class="empty-state"><p>Upload a group photo to see recognized students.</p></div>';
  }

  async function processGroupPhoto() {
    if (!state.groupPhotoFile) return;

    dom.btnProcessGroup.disabled = true;
    dom.btnProcessGroup.innerHTML = `<span>⏳</span> Processing Faces...`;

    const formData = new FormData();
    formData.append('file', state.groupPhotoFile);
    formData.append('session', dom.globalSession ? dom.globalSession.value : 'Morning');
    formData.append('subject', dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject);
    formData.append('tolerance', dom.groupTolerance ? parseFloat(dom.groupTolerance.value) / 100 : 0.55);

    try {
      const res = await fetch('/api/attendance/upload-group-photo', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Face recognition processing failed');
      const data = await res.json();

      playSuccessChime();
      showToast(`Group photo processed: ${data.total_faces} faces detected`, 'success');

      // Annotated image
      if (dom.annotatedDisplayImg && data.annotated_image) {
        dom.annotatedDisplayImg.src = data.annotated_image;
        if (dom.annotatedSection) dom.annotatedSection.classList.remove('hidden');
      }

      // Detection summary pills
      if (dom.groupStatsPills) {
        dom.groupStatsPills.classList.remove('hidden');
        if (dom.pillNewly) dom.pillNewly.textContent = data.newly_marked.length;
        if (dom.pillAlready) dom.pillAlready.textContent = data.already_marked.length;
        if (dom.pillUnknown) dom.pillUnknown.textContent = data.unknown_count;
      }

      // Populate Result List
      if (dom.groupResultList) {
        dom.groupResultList.innerHTML = '';
        const allRecognized = [...data.newly_marked, ...data.already_marked];
        if (allRecognized.length === 0) {
          dom.groupResultList.innerHTML = `<div class="empty-state"><p>No enrolled students matched. ${data.unknown_count} unknown face(s) found.</p></div>`;
        } else {
          allRecognized.forEach(s => {
            const isNew = data.newly_marked.some(m => m.student_id === s.student_id);
            const item = document.createElement('div');
            item.className = 'scan-log-item';
            item.innerHTML = `
              <div class="scan-avatar">${s.name.charAt(0)}</div>
              <div class="scan-info">
                <div class="scan-name">${s.name}</div>
                <div class="scan-meta">
                  <span>${s.roll_no}</span>
                  <span>•</span>
                  <span>${Math.round(s.confidence * 100)}% match</span>
                </div>
              </div>
              <div class="scan-tag ${isNew ? 'tag-new' : 'tag-repeat'}">${isNew ? 'Newly Marked' : 'Already Present'}</div>
            `;
            dom.groupResultList.appendChild(item);
          });
        }
      }

      loadDashboard(); // Refresh stats
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      if (dom.btnProcessGroup) {
        dom.btnProcessGroup.disabled = false;
        dom.btnProcessGroup.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> Process & Mark Attendance`;
      }
    }
  }

  /* ==========================================================================
     Register Student
     ========================================================================== */
  function setupRegistration() {
    if (!dom.studentRegForm) return;

    if (dom.btnModeFile) {
      dom.btnModeFile.addEventListener('click', () => {
        dom.btnModeFile.classList.add('active');
        dom.btnModeCam.classList.remove('active');
        if (dom.regFileSection) dom.regFileSection.classList.remove('hidden');
        if (dom.regCamSection) dom.regCamSection.classList.add('hidden');
        stopRegWebcam();
      });
    }

    if (dom.btnModeCam) {
      dom.btnModeCam.addEventListener('click', () => {
        dom.btnModeCam.classList.add('active');
        dom.btnModeFile.classList.remove('active');
        if (dom.regFileSection) dom.regFileSection.classList.add('hidden');
        if (dom.regCamSection) dom.regCamSection.classList.remove('hidden');
        startRegWebcam();
      });
    }

    if (dom.regPhotoFile) {
      dom.regPhotoFile.addEventListener('change', () => {
        const file = dom.regPhotoFile.files[0];
        if (file) {
          state.registrationPhotoBlob = file;
          if (dom.regFileLabel) dom.regFileLabel.textContent = file.name;
          showRegPreview(file);
        }
      });
    }

    if (dom.btnRegSnap) {
      dom.btnRegSnap.addEventListener('click', () => {
        if (!dom.regVideo || dom.regVideo.videoWidth === 0) return;
        const canvas = dom.regCanvas || document.createElement('canvas');
        canvas.width = dom.regVideo.videoWidth;
        canvas.height = dom.regVideo.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(dom.regVideo, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(blob => {
          state.registrationPhotoBlob = blob;
          showRegPreview(blob);
          if (dom.btnRegRetake) dom.btnRegRetake.classList.remove('hidden');
          showToast('Webcam snapshot captured', 'info', 1800);
        }, 'image/jpeg', 0.9);
      });
    }

    if (dom.btnRegRetake) {
      dom.btnRegRetake.addEventListener('click', () => {
        state.registrationPhotoBlob = null;
        if (dom.regPreviewBox) dom.regPreviewBox.classList.add('hidden');
        dom.btnRegRetake.classList.add('hidden');
      });
    }

    dom.studentRegForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const name = dom.regName.value.trim();
      const roll = dom.regRoll.value.trim();
      const prn = dom.regPrn.value.trim();

      if (!name || !roll || !prn) {
        showToast('Please fill all required student details', 'error');
        return;
      }
      if (!state.registrationPhotoBlob) {
        showToast('Please upload or snap a front-facing photo', 'error');
        return;
      }

      dom.btnSubmitReg.disabled = true;
      dom.btnSubmitReg.textContent = 'Enrolling & Training Model...';

      const formData = new FormData();
      formData.append('name', name);
      formData.append('roll_no', roll);
      formData.append('prn', prn);
      formData.append('photo', state.registrationPhotoBlob, `${roll}.jpg`);

      try {
        const res = await fetch('/api/students', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Enrollment failed');

        playSuccessChime();
        showToast(`Student "${name}" successfully registered!`, 'success');
        
        // Reset form
        dom.studentRegForm.reset();
        state.registrationPhotoBlob = null;
        if (dom.regPreviewBox) dom.regPreviewBox.classList.add('hidden');
        if (dom.regFileLabel) dom.regFileLabel.textContent = 'Click to select portrait photo (JPG, PNG)';
        stopRegWebcam();

        // Refresh system counts
        if (dom.trainedBadge) dom.trainedBadge.textContent = `${data.trained_faces} Enrolled`;
        loadDashboard();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        dom.btnSubmitReg.disabled = false;
        dom.btnSubmitReg.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Enroll & Train Face Model`;
      }
    });
  }

  function showRegPreview(fileOrBlob) {
    if (!dom.regAvatarImg || !dom.regPreviewBox) return;
    const url = URL.createObjectURL(fileOrBlob);
    dom.regAvatarImg.src = url;
    if (dom.previewName) dom.previewName.textContent = dom.regName.value || 'Student Name';
    if (dom.previewRoll) dom.previewRoll.textContent = dom.regRoll.value || 'Roll No';
    dom.regPreviewBox.classList.remove('hidden');
  }

  async function startRegWebcam() {
    try {
      state.regCamStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });
      if (dom.regVideo) {
        dom.regVideo.srcObject = state.regCamStream;
        dom.regVideo.play();
      }
    } catch (e) {
      showToast('Cannot access camera for enrollment', 'error');
    }
  }

  function stopRegWebcam() {
    if (state.regCamStream) {
      state.regCamStream.getTracks().forEach(t => t.stop());
      state.regCamStream = null;
    }
  }

  /* ==========================================================================
     Records & Reports
     ========================================================================== */
  async function loadRecords() {
    const date = dom.recFilterDate ? dom.recFilterDate.value : '';
    const session = dom.recFilterSession ? dom.recFilterSession.value : 'All';
    const subject = dom.recFilterSubject ? dom.recFilterSubject.value : 'All';
    const search = dom.recSearch ? dom.recSearch.value.trim() : '';

    let url = `/api/records?`;
    if (date) url += `date=${encodeURIComponent(date)}&`;
    if (session) url += `session=${encodeURIComponent(session)}&`;
    if (subject) url += `subject=${encodeURIComponent(subject)}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to load records');
      const data = await res.json();
      state.activeRecords = data.records || [];
      renderRecordsTable(state.activeRecords);
    } catch (err) {
      if (dom.recordsTableBody) {
        dom.recordsTableBody.innerHTML = `<tr><td colspan="9" class="loading-cell text-error">${err.message}</td></tr>`;
      }
    }
  }

  function renderRecordsTable(records) {
    if (!dom.recordsTableBody) return;
    if (records.length === 0) {
      dom.recordsTableBody.innerHTML = `<tr><td colspan="9" class="loading-cell">No records found for specified filters.</td></tr>`;
      return;
    }

    dom.recordsTableBody.innerHTML = '';
    records.forEach((r, idx) => {
      const isPresent = (r.status || 'Present') === 'Present';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><strong>${r.name || '--'}</strong></td>
        <td><code>${r.roll_no || '--'}</code></td>
        <td><code>${r.prn || '--'}</code></td>
        <td>${r.date || '--'}</td>
        <td>${r.time || '--'}</td>
        <td>${r.session || '--'}</td>
        <td>${r.subject || 'General'}</td>
        <td>
          <span class="status-pill ${isPresent ? 'status-present' : 'status-absent'}">
            <span class="status-dot"></span>
            ${isPresent ? 'Present' : 'Absent'}
          </span>
        </td>
      `;
      dom.recordsTableBody.appendChild(tr);
    });
  }

  window.exportData = function (format) {
    const date = dom.recFilterDate && dom.recFilterDate.value ? dom.recFilterDate.value : (dom.globalDate ? dom.globalDate.value : state.meta.today);
    const session = dom.recFilterSession ? dom.recFilterSession.value : 'All';
    const subject = dom.recFilterSubject ? dom.recFilterSubject.value : 'All';

    const url = `/api/export?format=${format}&date=${encodeURIComponent(date)}&session=${encodeURIComponent(session)}&subject=${encodeURIComponent(subject)}`;
    showToast(`Generating ${format.toUpperCase()} report download...`, 'info', 2500);
    window.location.href = url;
  };

  window.exportDefaulters = function (format = 'excel') {
    const threshSlider = document.getElementById('defaulter-threshold-slider');
    const threshold = threshSlider ? threshSlider.value : 75;
    const subSelect = document.getElementById('defaulter-filter-subject') || dom.recFilterSubject;
    const subject = subSelect ? subSelect.value : 'All';
    const url = `/api/export/defaulters?threshold=${threshold}&format=${format}&subject=${encodeURIComponent(subject)}`;
    showToast(`Generating Defaulters (< ${threshold}%) Report...`, 'info', 3000);
    window.location.href = url;
  };

  window.exportMonthlyMatrix = function () {
    const monthSelect = document.getElementById('matrix-month');
    const yearSelect = document.getElementById('matrix-year');
    const subjectSelect = document.getElementById('matrix-subject') || dom.recFilterSubject;

    const cur = new Date();
    const month = monthSelect && monthSelect.value ? monthSelect.value : (cur.getMonth() + 1);
    const year = yearSelect && yearSelect.value ? yearSelect.value : cur.getFullYear();
    const subject = subjectSelect ? subjectSelect.value : 'All';

    const url = `/api/export/monthly-matrix?year=${year}&month=${month}&subject=${encodeURIComponent(subject)}`;
    showToast(`Generating Monthly Register Matrix (${month}/${year})...`, 'info', 3000);
    window.location.href = url;
  };

  window.backupDatabase = function () {
    showToast('Preparing full database & encodings backup...', 'info', 2500);
    window.location.href = '/api/system/backup';
  };

  window.downloadSampleTemplate = function () {
    showToast('Downloading student roster template...', 'info', 2000);
    window.location.href = '/api/students/sample-template';
  };

  window.exportAbsenteeCsv = function () {
    const date = dom.globalDate ? dom.globalDate.value : state.meta.today;
    const session = dom.globalSession ? dom.globalSession.value : 'Morning';
    const subject = dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject;
    window.location.href = `/api/notifications/absentees/csv?date=${encodeURIComponent(date)}&session=${encodeURIComponent(session)}&subject=${encodeURIComponent(subject)}`;
    showToast('Downloading absentee dispatch CSV...', 'info', 2000);
  };

  /* ==========================================================================
     Absentee Notifications Modal
     ========================================================================== */
  window.openAbsenteeModal = async function () {
    const modal = document.getElementById('absentee-modal');
    const list = document.getElementById('absentee-list');
    const sub = document.getElementById('absentee-modal-sub');
    if (!modal || !list) return;

    modal.classList.remove('hidden');
    list.innerHTML = '<div class="loading-cell">Loading absent students and generating notices...</div>';

    const date = dom.globalDate ? dom.globalDate.value : state.meta.today;
    const session = dom.globalSession ? dom.globalSession.value : 'Morning';
    const subject = dom.globalSubject ? dom.globalSubject.value : state.meta.default_subject;

    if (sub) {
      sub.textContent = `${date} • ${session} Session • ${subject}`;
    }

    try {
      const res = await fetch(`/api/notifications/absentees?date=${encodeURIComponent(date)}&session=${encodeURIComponent(session)}&subject=${encodeURIComponent(subject)}`);
      if (!res.ok) throw new Error('Failed to fetch absentee notices');
      const data = await res.json();

      if (!data.notices || data.notices.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>🎉 100% Attendance! No students are absent for this session.</p></div>';
        return;
      }

      list.innerHTML = '';
      data.notices.forEach(n => {
        const item = document.createElement('div');
        item.className = 'absentee-item';
        item.innerHTML = `
          <div class="absentee-meta">
            <div>
              <span class="absentee-name">${n.name}</span>
              <span class="absentee-roll"> • Roll: ${n.roll_no} (PRN: ${n.prn})</span>
            </div>
            <span class="status-pill status-absent">Absent</span>
          </div>
          <div class="absentee-preview-msg">${escapeHtml(n.whatsapp_text)}</div>
          <div class="absentee-actions">
            <a href="${n.whatsapp_url}" target="_blank" rel="noopener noreferrer" class="btn-whatsapp">
              💬 Send WhatsApp
            </a>
            <button class="btn btn-secondary btn-sm" onclick="copyNoticeText('${escapeQuotes(n.sms_text)}')">
              📋 Copy SMS
            </button>
            <button class="btn btn-secondary btn-sm" onclick="copyNoticeText('${escapeQuotes(n.email_body)}')">
              ✉️ Copy Email
            </button>
          </div>
        `;
        list.appendChild(item);
      });
    } catch (e) {
      list.innerHTML = `<div class="empty-state text-error">${e.message}</div>`;
    }
  };

  window.closeAbsenteeModal = function () {
    const modal = document.getElementById('absentee-modal');
    if (modal) modal.classList.add('hidden');
  };

  window.copyNoticeText = function (text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('Message copied to clipboard!', 'success', 2000);
    }).catch(() => {
      showToast('Failed to copy to clipboard', 'error');
    });
  };

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /* ==========================================================================
     Academic Analytics & Defaulters
     ========================================================================== */
  async function loadAnalytics() {
    const threshSlider = document.getElementById('defaulter-threshold-slider');
    const threshLabel = document.getElementById('defaulter-thresh-label');
    const threshVal = threshSlider ? threshSlider.value : 75;
    if (threshLabel) threshLabel.textContent = `${threshVal}%`;

    const subSelect = document.getElementById('defaulter-filter-subject');
    const subject = subSelect ? subSelect.value : 'All';

    const tbody = document.getElementById('defaulters-table-body');
    if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="loading-cell">Evaluating academic attendance records...</td></tr>';

    try {
      const url = `/api/analytics/defaulters?threshold=${threshVal}&subject=${encodeURIComponent(subject)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to load defaulters analysis');
      const data = await res.json();

      const defCountEl = document.getElementById('analytic-defaulter-count');
      const defThreshEl = document.getElementById('analytic-def-thresh');
      const totalStudentsEl = document.getElementById('analytic-total-students');
      const eligibleCountEl = document.getElementById('analytic-eligible-count');
      const sessionsHeldEl = document.getElementById('analytic-sessions-held');

      if (defCountEl) defCountEl.textContent = data.defaulters_count;
      if (defThreshEl) defThreshEl.textContent = data.threshold;
      if (totalStudentsEl) totalStudentsEl.textContent = data.total_students;
      if (eligibleCountEl) eligibleCountEl.textContent = Math.max(0, data.total_students - data.defaulters_count);
      
      const maxHeld = data.defaulters.length > 0 ? data.defaulters[0].total_held : 0;
      if (sessionsHeldEl) sessionsHeldEl.textContent = maxHeld;

      renderDefaultersTable(data.defaulters);
    } catch (e) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="9" class="empty-state text-error">${e.message}</td></tr>`;
    }
  }

  function renderDefaultersTable(defaulters) {
    const tbody = document.getElementById('defaulters-table-body');
    if (!tbody) return;

    const query = document.getElementById('defaulter-search-input') ? document.getElementById('defaulter-search-input').value.trim().toLowerCase() : '';
    const filtered = defaulters.filter(d => {
      if (!query) return true;
      return (
        (d.name || '').toLowerCase().includes(query) ||
        (d.roll_no || '').toLowerCase().includes(query) ||
        (d.prn || '').toLowerCase().includes(query)
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-state"><p>🎉 Excellent! No defaulters found below threshold.</p></td></tr>';
      return;
    }

    tbody.innerHTML = '';
    filtered.forEach((d, idx) => {
      const tr = document.createElement('tr');
      const isCritical = d.percentage < 65.0;
      const riskClass = isCritical ? 'risk-critical' : 'risk-warning';
      const riskText = isCritical ? 'Critical (<65%)' : 'Warning (<75%)';
      const barColor = isCritical ? '#ef4444' : '#f59e0b';

      const warningText = encodeURIComponent(
        `📢 *Attendance Warning — Academic Office*\n\n` +
        `Dear Parent / Student,\n` +
        `This is an official notice regarding the attendance of *${d.name}* (Roll: *${d.roll_no}*).\n` +
        `Current Attendance: *${d.percentage}%* (${d.attended}/${d.total_held} lectures).\n` +
        `As per institutional norms, minimum 75% attendance is mandatory to appear for exams.\n` +
        `Please meet the Academic Coordinator immediately.`
      );
      const waUrl = d.phone
        ? `https://api.whatsapp.com/send?phone=${d.phone}&text=${warningText}`
        : `https://api.whatsapp.com/send?text=${warningText}`;

      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>
          <div style="font-weight:700;cursor:pointer;color:var(--accent-primary);" onclick="openStudentProfile(${d.student_id})">
            ${d.name}
          </div>
        </td>
        <td><code>${d.roll_no}</code></td>
        <td><code>${d.prn}</code></td>
        <td><strong>${d.attended}</strong> / ${d.total_held}</td>
        <td>
          <div style="font-weight:800;color:${barColor}">${d.percentage}%</div>
          <div class="mini-progress-track">
            <div class="mini-progress-fill" style="width:${Math.min(100, d.percentage)}%;background:${barColor};"></div>
          </div>
        </td>
        <td><span class="risk-pill ${riskClass}">${riskText}</span></td>
        <td style="font-size:12px;color:var(--text-secondary);">${d.phone || d.email || '--'}</td>
        <td>
          <a href="${waUrl}" target="_blank" rel="noopener noreferrer" class="btn-whatsapp" title="Send WhatsApp Warning">
            💬 WhatsApp Notice
          </a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  /* ==========================================================================
     Monthly Register Matrix
     ========================================================================== */
  async function loadMonthlyMatrix() {
    const monthSelect = document.getElementById('matrix-month');
    const yearSelect = document.getElementById('matrix-year');
    const subjectSelect = document.getElementById('matrix-subject');

    const month = monthSelect ? monthSelect.value : (new Date().getMonth() + 1);
    const year = yearSelect ? yearSelect.value : new Date().getFullYear();
    const subject = subjectSelect ? subjectSelect.value : 'All';

    const wrapper = document.getElementById('matrix-wrapper');
    if (wrapper) wrapper.innerHTML = '<div class="loading-cell">Loading monthly attendance register matrix...</div>';

    try {
      const url = `/api/analytics/monthly-matrix?year=${year}&month=${month}&subject=${encodeURIComponent(subject)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch monthly matrix');
      const data = await res.json();
      renderMatrixTable(data);
    } catch (e) {
      if (wrapper) wrapper.innerHTML = `<div class="empty-state text-error">${e.message}</div>`;
    }
  }

  function renderMatrixTable(matrixData) {
    const wrapper = document.getElementById('matrix-wrapper');
    if (!wrapper) return;

    if (!matrixData.rows || matrixData.rows.length === 0) {
      wrapper.innerHTML = '<div class="empty-state"><p>No enrolled students found in database.</p></div>';
      return;
    }

    const heldDays = matrixData.held_days || [];
    let headerHtml = `
      <table class="matrix-table">
        <thead>
          <tr>
            <th class="sticky-col" style="min-width:140px;">Student Name</th>
            <th class="sticky-col-2" style="min-width:110px;">Roll No</th>
    `;

    for (let day = 1; day <= 31; day++) {
      const isHeld = heldDays.includes(day);
      const style = isHeld ? 'color:#a78bfa;font-weight:800;background:#1e1b4b;' : 'opacity:0.5;';
      headerHtml += `<th style="${style}">${day}</th>`;
    }

    headerHtml += `
            <th style="min-width:70px;">Attended</th>
            <th style="min-width:70px;">Held</th>
            <th style="min-width:80px;">Month %</th>
          </tr>
        </thead>
        <tbody>
    `;

    matrixData.rows.forEach(r => {
      const pctColor = r.percentage >= 75 ? '#34d399' : (r.percentage >= 65 ? '#fbbf24' : '#f87171');
      headerHtml += `
        <tr>
          <td class="sticky-col">
            <span style="font-weight:700;cursor:pointer;" onclick="openStudentProfile(${r.student_id})">${r.name}</span>
          </td>
          <td class="sticky-col-2"><code>${r.roll_no}</code></td>
      `;

      for (let day = 1; day <= 31; day++) {
        const st = r.days[day];
        if (st === 'P') {
          headerHtml += `<td><span class="badge-p">P</span></td>`;
        } else if (st === 'A') {
          headerHtml += `<td><span class="badge-a">A</span></td>`;
        } else {
          headerHtml += `<td><span class="badge-na">-</span></td>`;
        }
      }

      headerHtml += `
          <td><strong>${r.attended}</strong></td>
          <td>${r.total_held}</td>
          <td><strong style="color:${pctColor}">${r.percentage}%</strong></td>
        </tr>
      `;
    });

    headerHtml += `</tbody></table>`;
    wrapper.innerHTML = headerHtml;
  }

  /* ==========================================================================
     Student Self-Service Portal
     ========================================================================== */
  window.lookupStudentPortal = async function () {
    const input = document.getElementById('portal-query');
    if (!input || !input.value.trim()) return;
    const query = input.value.trim();

    const resCard = document.getElementById('portal-result-card');
    if (!resCard) return;

    resCard.classList.remove('hidden');
    resCard.innerHTML = '<div class="loading-cell">Searching academic records for ' + escapeHtml(query) + '...</div>';

    try {
      const res = await fetch(`/api/student-portal/lookup?query=${encodeURIComponent(query)}`);
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Student not found');
      }
      const data = await res.json();
      renderStudentPortalReport(data);
    } catch (e) {
      resCard.innerHTML = `
        <div class="empty-state text-error" style="background:rgba(239,68,68,0.1);padding:24px;border-radius:var(--radius-xl);border:1px solid rgba(239,68,68,0.3);">
          <h3>❌ ${e.message}</h3>
          <p style="margin-top:6px;color:var(--text-secondary);">Please double-check your Roll Number or PRN and try again.</p>
        </div>
      `;
    }
  };

  function renderStudentPortalReport(data) {
    const resCard = document.getElementById('portal-result-card');
    if (!resCard) return;

    const s = data.student;
    const overallPct = data.overall_percentage;
    const isDef = data.is_defaulter;
    const meterColor = overallPct >= 75 ? '#10b981' : (overallPct >= 65 ? '#f59e0b' : '#ef4444');
    const statusPillClass = overallPct >= 75 ? 'status-present' : 'status-absent';
    const statusMsg = overallPct >= 75 ? '✅ Safe & Eligible' : '⚠️ Defaulter Alert (<75%)';

    const avatar = s.photo_url
      ? `<img src="${s.photo_url}" class="portal-avatar-img" alt="${s.name}">`
      : `<div class="portal-avatar-img" style="display:flex;align-items:center;justify-content:center;font-size:48px;background:#1e293b;">👨‍🎓</div>`;

    let subjsHtml = '';
    (data.subject_breakdown || []).forEach(sub => {
      const subColor = sub.percentage >= 75 ? '#10b981' : (sub.percentage >= 65 ? '#f59e0b' : '#ef4444');
      subjsHtml += `
        <div class="portal-subj-card">
          <div class="portal-subj-name">${sub.subject}</div>
          <div class="portal-subj-count">
            <span>Attended: <strong>${sub.attended}</strong> / ${sub.held}</span>
            <span style="font-weight:800;color:${subColor}">${sub.percentage}%</span>
          </div>
          <div class="mini-progress-track" style="width:100%;">
            <div class="mini-progress-fill" style="width:${Math.min(100, sub.percentage)}%;background:${subColor};"></div>
          </div>
        </div>
      `;
    });

    let logsHtml = '';
    (data.recent_logs || []).slice(0, 15).forEach(l => {
      const isPres = (l.status || 'Present') === 'Present';
      logsHtml += `
        <tr>
          <td>${l.date}</td>
          <td>${l.session}</td>
          <td>${l.subject || 'General'}</td>
          <td>${l.time || '--'}</td>
          <td>
            <span class="status-pill ${isPres ? 'status-present' : 'status-absent'}">
              ${isPres ? 'Present' : 'Absent'}
            </span>
          </td>
        </tr>
      `;
    });

    resCard.innerHTML = `
      <div class="portal-hero-card">
        ${avatar}
        <div class="portal-details">
          <h3>${s.name}</h3>
          <div class="portal-meta-badges">
            <span class="code-badge">Roll: ${s.roll_no}</span>
            <span class="code-badge">PRN: ${s.prn}</span>
            <span class="status-pill ${statusPillClass}">${statusMsg}</span>
          </div>
          <p style="color:var(--text-secondary);font-size:13px;">
            ${s.email ? '✉️ ' + s.email : ''} ${s.phone ? '• 📞 ' + s.phone : ''}
          </p>
          <div style="margin-top:14px;">
            <button class="btn btn-secondary btn-sm" onclick="window.print()">
              🖨️ Print / Save Report
            </button>
          </div>
        </div>
        <div class="portal-meter-col">
          <div class="portal-meter-value" style="color:${meterColor}">${overallPct}%</div>
          <div class="portal-meter-label">Overall Attendance</div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:6px;">
            ${data.attended} / ${data.total_held} Sessions Attended
          </div>
        </div>
      </div>

      <div class="card glass-card" style="margin-top:16px;">
        <div class="card-header">
          <h3>Subject-wise Attendance Breakdown</h3>
        </div>
        <div class="portal-subj-grid">
          ${subjsHtml}
        </div>
      </div>

      <div class="card glass-card" style="margin-top:16px;">
        <div class="card-header">
          <h3>Recent Session Log</h3>
        </div>
        <div class="table-responsive">
          <table class="modern-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Session</th>
                <th>Subject</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${logsHtml || '<tr><td colspan="5" class="loading-cell">No recent sessions found.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  /* ==========================================================================
     Student Profile & Edit Modal
     ========================================================================== */
  let activeStudentProfileId = null;

  window.openStudentProfile = async function (studentId) {
    activeStudentProfileId = studentId;
    const modal = document.getElementById('student-profile-modal');
    if (!modal) return;
    modal.classList.remove('hidden');

    try {
      const res = await fetch(`/api/students/${studentId}`);
      if (!res.ok) throw new Error('Failed to load student details');
      const data = await res.json();
      const s = data.student;

      document.getElementById('modal-student-name').textContent = s.name;
      document.getElementById('modal-student-sub').textContent = `Roll No: ${s.roll_no} • PRN: ${s.prn}`;
      document.getElementById('modal-profile-fullname').textContent = s.name;
      document.getElementById('modal-profile-roll').textContent = `Roll: ${s.roll_no}`;
      document.getElementById('modal-profile-prn').textContent = `PRN: ${s.prn}`;

      const pctPill = document.getElementById('modal-profile-status-pill');
      if (pctPill) {
        pctPill.textContent = `${data.overall_percentage}% Attendance (${data.attended}/${data.total_held})`;
        pctPill.className = `status-pill ${data.overall_percentage >= 75 ? 'status-present' : 'status-absent'}`;
      }

      const contactRow = document.getElementById('modal-profile-contact');
      if (contactRow) {
        contactRow.innerHTML = `<span>📞 ${s.phone || 'No phone'}</span> • <span>✉️ ${s.email || 'No email'}</span>`;
      }

      const avatarImg = document.getElementById('modal-profile-avatar');
      if (avatarImg) {
        if (s.photo_url) {
          avatarImg.src = s.photo_url;
          avatarImg.style.display = 'block';
        } else {
          avatarImg.src = '';
          avatarImg.style.display = 'none';
        }
      }

      // Populate breakdown grid
      const subjGrid = document.getElementById('modal-subject-breakdown-grid');
      if (subjGrid) {
        subjGrid.innerHTML = '';
        (data.subject_breakdown || []).forEach(sub => {
          const color = sub.percentage >= 75 ? '#10b981' : (sub.percentage >= 65 ? '#f59e0b' : '#ef4444');
          const card = document.createElement('div');
          card.className = 'portal-subj-card';
          card.innerHTML = `
            <div class="portal-subj-name">${sub.subject}</div>
            <div class="portal-subj-count">
              <span>${sub.attended}/${sub.held}</span>
              <strong style="color:${color}">${sub.percentage}%</strong>
            </div>
            <div class="mini-progress-track" style="width:100%;">
              <div class="mini-progress-fill" style="width:${Math.min(100, sub.percentage)}%;background:${color};"></div>
            </div>
          `;
          subjGrid.appendChild(card);
        });
      }

      // Populate recent logs
      const logsBody = document.getElementById('modal-recent-logs-body');
      if (logsBody) {
        logsBody.innerHTML = '';
        (data.recent_logs || []).forEach(l => {
          const isP = (l.status || 'Present') === 'Present';
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${l.date}</td>
            <td>${l.session}</td>
            <td>${l.subject || 'General'}</td>
            <td>${l.time || '--'}</td>
            <td><span class="status-pill ${isP ? 'status-present' : 'status-absent'}">${isP ? 'P' : 'A'}</span></td>
          `;
          logsBody.appendChild(tr);
        });
      }

      // Populate edit form
      document.getElementById('edit-student-id').value = s.id;
      document.getElementById('edit-first-name').value = s.first_name || '';
      document.getElementById('edit-middle-name').value = s.middle_name || '';
      document.getElementById('edit-last-name').value = s.last_name || '';
      document.getElementById('edit-roll-no').value = s.roll_no || '';
      document.getElementById('edit-prn').value = s.prn || '';
      document.getElementById('edit-phone').value = s.phone || '';
      document.getElementById('edit-email').value = s.email || '';

      // Populate Cyber Hologram ID Card
      const idName = document.getElementById('id-badge-name');
      const idRoll = document.getElementById('id-badge-roll');
      const idPrn = document.getElementById('id-badge-prn');
      const idStatus = document.getElementById('id-badge-status');
      const idPhoto = document.getElementById('id-badge-photo');
      const idChip = document.getElementById('id-badge-chip');
      if (idName) idName.textContent = s.name.toUpperCase();
      if (idRoll) idRoll.textContent = s.roll_no || '--';
      if (idPrn) idPrn.textContent = s.prn || '--';
      if (idStatus) {
        const eligible = (data.overall_percentage || 0) >= 75;
        idStatus.textContent = eligible ? `EXAM ELIGIBLE (${data.overall_percentage}%)` : `DEFAULTER NOTICE (${data.overall_percentage}%)`;
        idStatus.className = `v ${eligible ? 'status-active' : 'status-danger'}`;
      }
      if (idPhoto) {
        idPhoto.src = s.photo_url || '';
        idPhoto.style.display = s.photo_url ? 'block' : 'none';
      }
      if (idChip) {
        idChip.textContent = `BIO-${s.roll_no || s.id}-SEC`;
      }
      drawCyberQrCode(`STUDENT:${s.name}|ROLL:${s.roll_no}|PRN:${s.prn}|ATT:${data.overall_percentage}%`);

      switchProfileSubtab('profile-tab-overview');
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  window.closeStudentProfileModal = function () {
    const modal = document.getElementById('student-profile-modal');
    if (modal) modal.classList.add('hidden');
    activeStudentProfileId = null;
  };

  window.switchProfileSubtab = function (subtabId) {
    document.querySelectorAll('.profile-subtab').forEach(b => {
      b.classList.toggle('active', b.dataset.subtab === subtabId);
    });
    document.querySelectorAll('.profile-subtab-pane').forEach(p => {
      p.classList.toggle('active', p.id === subtabId);
      p.classList.toggle('hidden', p.id !== subtabId);
    });
  };

  window.saveStudentProfile = async function () {
    const sid = document.getElementById('edit-student-id').value;
    if (!sid) return;

    const payload = {
      first_name: document.getElementById('edit-first-name').value.trim(),
      middle_name: document.getElementById('edit-middle-name').value.trim(),
      last_name: document.getElementById('edit-last-name').value.trim(),
      roll_no: document.getElementById('edit-roll-no').value.trim(),
      prn: document.getElementById('edit-prn').value.trim(),
      phone: document.getElementById('edit-phone').value.trim(),
      email: document.getElementById('edit-email').value.trim()
    };

    try {
      const res = await fetch(`/api/students/${sid}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Update failed');

      showToast('Student information updated successfully!', 'success');
      loadStudents();
      loadDashboard();
      openStudentProfile(sid);
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  window.deleteStudentFromModal = function () {
    const sid = document.getElementById('edit-student-id').value;
    const name = document.getElementById('modal-profile-fullname').textContent;
    closeStudentProfileModal();
    window.deleteStudent(sid, name);
  };

  /* ==========================================================================
     Bulk Import Modal Handlers
     ========================================================================== */
  window.openBulkImportModal = function () {
    const modal = document.getElementById('bulk-import-modal');
    if (modal) {
      modal.classList.remove('hidden');
      const st = document.getElementById('bulk-import-status');
      if (st) {
        st.classList.add('hidden');
        st.innerHTML = '';
      }
    }
  };

  window.closeBulkImportModal = function () {
    const modal = document.getElementById('bulk-import-modal');
    if (modal) modal.classList.add('hidden');
  };

  async function handleBulkUploadFile(file) {
    if (!file) return;
    const statusBox = document.getElementById('bulk-import-status');
    if (statusBox) {
      statusBox.classList.remove('hidden');
      statusBox.innerHTML = '<div class="loading-cell">Processing spreadsheet and validating student records...</div>';
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/students/bulk-import', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Bulk import failed');

      playSuccessChime();
      let statusHtml = `
        <div style="color:#34d399;font-weight:700;margin-bottom:6px;">
          ✅ Successfully enrolled ${data.imported} new student(s)!
        </div>
      `;
      if (data.skipped > 0) {
        statusHtml += `<div style="color:#fbbf24;font-size:12px;">• ${data.skipped} duplicate student(s) skipped.</div>`;
      }
      if (data.errors && data.errors.length > 0) {
        statusHtml += `<div style="color:#f87171;font-size:12px;margin-top:6px;">⚠️ Validation notices:<ul style="padding-left:18px;">`;
        data.errors.slice(0, 5).forEach(err => {
          statusHtml += `<li>${escapeHtml(err)}</li>`;
        });
        statusHtml += `</ul></div>`;
      }

      if (statusBox) statusBox.innerHTML = statusHtml;
      showToast(`Import completed: ${data.imported} enrolled!`, 'success', 3000);

      if (dom.trainedBadge) dom.trainedBadge.textContent = `${data.total_enrolled} Enrolled`;
      loadStudents();
      loadDashboard();
    } catch (e) {
      if (statusBox) {
        statusBox.innerHTML = `<div style="color:#f87171;font-weight:700;">❌ ${escapeHtml(e.message)}</div>`;
      }
      showToast(e.message, 'error');
    }
  }

  /* ==========================================================================
     Student Directory
     ========================================================================== */
  async function loadStudents() {
    try {
      const res = await fetch('/api/students');
      if (!res.ok) throw new Error('Failed to load student directory');
      const data = await res.json();
      state.allStudents = data.students || [];

      if (dom.dirCountText) {
        dom.dirCountText.textContent = `${state.allStudents.length} Students Enrolled`;
      }
      renderStudentGrid(state.allStudents);
    } catch (e) {
      if (dom.studentsGrid) {
        dom.studentsGrid.innerHTML = `<div class="empty-state text-error">${e.message}</div>`;
      }
    }
  }

  function renderStudentGrid(students) {
    if (!dom.studentsGrid) return;
    const query = dom.dirSearch ? dom.dirSearch.value.trim().toLowerCase() : '';
    const filtered = students.filter(s => {
      if (!query) return true;
      return (
        s.name.toLowerCase().includes(query) ||
        s.roll_no.toLowerCase().includes(query) ||
        s.prn.toLowerCase().includes(query)
      );
    });

    if (filtered.length === 0) {
      dom.studentsGrid.innerHTML = `<div class="empty-state"><p>No students found matching search.</p></div>`;
      return;
    }

    dom.studentsGrid.innerHTML = '';
    filtered.forEach(s => {
      const card = document.createElement('div');
      card.className = 'student-card';

      const avatarHtml = s.photo_url
        ? `<img src="${s.photo_url}" class="student-card-avatar" alt="${s.name}" onerror="this.onerror=null;this.src='';">`
        : `<div class="student-card-avatar" style="display:flex;align-items:center;justify-content:center;font-size:32px;">👤</div>`;

      card.innerHTML = `
        ${avatarHtml}
        <div class="student-card-info" style="cursor:pointer;" onclick="openStudentProfile(${s.id})">
          <h4>${s.name}</h4>
          <div class="card-roll">${s.roll_no}</div>
          <div class="card-prn">PRN: ${s.prn}</div>
        </div>
        <div class="student-card-actions">
          <button class="btn btn-secondary btn-xs" style="padding:4px 10px;font-size:11px;" onclick="openStudentProfile(${s.id})">
            Profile & Stats
          </button>
          <button class="btn-delete-student" onclick="deleteStudent(${s.id}, '${escapeQuotes(s.name)}')">
            Delete
          </button>
        </div>
      `;
      dom.studentsGrid.appendChild(card);
    });
  }

  function escapeQuotes(str) {
    return (str || '').replace(/'/g, "\\'");
  }

  window.deleteStudent = async function (id, name) {
    if (!confirm(`Are you sure you want to delete "${name}" and all their attendance records?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/students/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Deletion failed');
      const data = await res.json();
      showToast(`Student "${name}" deleted.`, 'success');

      if (dom.trainedBadge) dom.trainedBadge.textContent = `${data.trained_faces} Enrolled`;
      loadStudents();
      loadDashboard();
    } catch (e) {
      showToast(e.message, 'error');
    }
  };

  /* ==========================================================================
     Retrain Model
     ========================================================================== */
  async function retrainAll() {
    if (dom.btnRetrain) {
      dom.btnRetrain.disabled = true;
      dom.btnRetrain.classList.add('loading');
    }
    showToast('Re-encoding all student faces... please wait', 'info', 4000);

    try {
      const res = await fetch('/api/retrain', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error('Retraining failed');

      showToast(`Retrain Complete! ${data.trained} faces active`, 'success');
      if (dom.trainedBadge) dom.trainedBadge.textContent = `${data.total_active_encodings} Enrolled`;
      loadDashboard();
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      if (dom.btnRetrain) {
        dom.btnRetrain.disabled = false;
        dom.btnRetrain.classList.remove('loading');
      }
    }
  }

  /* ==========================================================================
     Event Listeners Attachment
     ========================================================================== */
  function attachEventListeners() {
    // Nav Tabs
    dom.navTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        window.switchTab(tab.dataset.tab);
      });
    });

    // Sound toggle
    if (dom.btnSoundToggle) {
      dom.btnSoundToggle.addEventListener('click', () => {
        state.audioEnabled = !state.audioEnabled;
        if (state.audioEnabled) {
          dom.btnSoundToggle.classList.add('active');
          if (dom.soundIcon) dom.soundIcon.textContent = '🔊';
          showToast('Audio chime enabled', 'info', 1500);
        } else {
          dom.btnSoundToggle.classList.remove('active');
          if (dom.soundIcon) dom.soundIcon.textContent = '🔇';
          showToast('Audio chime muted', 'info', 1500);
        }
      });
    }

    // J.A.R.V.I.S. AI Voice Controls & Holographic Command Console
    if (dom.btnJarvisSpeakTest) {
      dom.btnJarvisSpeakTest.addEventListener('click', testJarvisVoice);
    }

    if (dom.btnJarvisAnnounceSummary) {
      dom.btnJarvisAnnounceSummary.addEventListener('click', announceAttendanceSummary);
    }

    if (dom.btnJarvisToggleVoice) {
      dom.btnJarvisToggleVoice.addEventListener('click', toggleJarvisVoice);
    }

    // Floating Orb and Header buttons open Command Console Modal
    if (dom.jarvisFloatingOrb) {
      dom.jarvisFloatingOrb.addEventListener('click', openJarvisModal);
    }
    if (dom.btnJarvisGlobal) {
      dom.btnJarvisGlobal.addEventListener('click', openJarvisModal);
    }

    // Modal Close
    if (dom.jarvisConsoleClose) {
      dom.jarvisConsoleClose.addEventListener('click', closeJarvisModal);
    }
    if (dom.jarvisConsoleModal) {
      dom.jarvisConsoleModal.addEventListener('click', (e) => {
        if (e.target === dom.jarvisConsoleModal) closeJarvisModal();
      });
    }

    // Text Command input
    if (dom.btnJarvisSend && dom.jarvisTextCmd) {
      dom.btnJarvisSend.addEventListener('click', () => {
        const val = dom.jarvisTextCmd.value;
        if (val && val.trim()) {
          executeJarvisCommand(val);
          dom.jarvisTextCmd.value = '';
        }
      });
      dom.jarvisTextCmd.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const val = dom.jarvisTextCmd.value;
          if (val && val.trim()) {
            executeJarvisCommand(val);
            dom.jarvisTextCmd.value = '';
          }
        }
      });
    }

    // Command chips inside modal
    document.querySelectorAll('.chip-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.getAttribute('data-command');
        if (cmd) executeJarvisCommand(cmd);
      });
    });

    // Clear dialogue log
    if (dom.btnClearJarvisLog && dom.jarvisLogStream) {
      dom.btnClearJarvisLog.addEventListener('click', () => {
        dom.jarvisLogStream.innerHTML = '';
        appendJarvisLog('J.A.R.V.I.S.', 'Dialogue log cleared. Systems standing by.');
      });
    }

    // Start Oscilloscope visualizer and Voice Recognition
    startOscilloscopeRenderer();
    setupSpeechRecognition();

    // Projection Mode HUD Controls
    if (dom.btnProjectionMode) {
      dom.btnProjectionMode.addEventListener('click', openProjectionMode);
    }
    if (dom.btnCloseProjection) {
      dom.btnCloseProjection.addEventListener('click', closeProjectionMode);
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && state.inProjectionMode) {
        closeProjectionMode();
      }
    });

    // Hands-Free Wake-Word Chip
    if (dom.btnChipHandsFree) {
      dom.btnChipHandsFree.addEventListener('click', toggleHandsFreeJarvis);
    }

    // 3D Parallax Tilt for Cyber ID Card
    setupCyberCardTilt();

    // Expose global methods
    window.openProjectionMode = openProjectionMode;
    window.closeProjectionMode = closeProjectionMode;
    window.toggleHandsFreeJarvis = toggleHandsFreeJarvis;
    window.drawCyberQrCode = drawCyberQrCode;

    // Global filters change
    [dom.globalDate, dom.globalSession, dom.globalSubject].forEach(el => {
      if (el) el.addEventListener('change', loadDashboard);
    });

    if (dom.btnDashRefresh) {
      dom.btnDashRefresh.addEventListener('click', loadDashboard);
    }

    if (dom.dashSearch) {
      dom.dashSearch.addEventListener('input', () => {
        loadDashboard();
      });
    }

    // Camera buttons
    if (dom.btnStartCamera) dom.btnStartCamera.addEventListener('click', startWebcam);
    if (dom.btnToggleCamera) {
      dom.btnToggleCamera.addEventListener('click', () => {
        if (state.cameraScanning) {
          stopWebcam();
          dom.btnToggleCamera.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg> Start Camera`;
        } else {
          startWebcam();
          dom.btnToggleCamera.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg> Stop Camera`;
        }
      });
    }

    if (dom.btnAutoScan) {
      dom.btnAutoScan.addEventListener('click', () => {
        state.autoScanActive = !state.autoScanActive;
        if (state.autoScanActive) {
          dom.btnAutoScan.classList.add('active-mode');
          dom.btnAutoScan.innerHTML = `<span class="status-indicator-dot"></span> Auto-Scan Active (1.5s)`;
        } else {
          dom.btnAutoScan.classList.remove('active-mode');
          dom.btnAutoScan.innerHTML = `<span class="status-indicator-dot" style="background:#9CA3AF"></span> Auto-Scan Paused`;
        }
      });
    }

    if (dom.btnManualSnap) {
      dom.btnManualSnap.addEventListener('click', () => {
        if (!state.cameraScanning) {
          showToast('Please start camera first', 'info');
          return;
        }
        captureAndRecognizeFrame();
        showToast('Scanning frame...', 'info', 1000);
      });
    }

    if (dom.camTolerance) {
      dom.camTolerance.addEventListener('input', () => {
        if (dom.camToleranceVal) {
          dom.camToleranceVal.textContent = `${dom.camTolerance.value}%`;
        }
      });
    }

    // Retrain button
    if (dom.btnRetrain) dom.btnRetrain.addEventListener('click', retrainAll);

    // Records
    if (dom.btnApplyRecFilters) dom.btnApplyRecFilters.addEventListener('click', loadRecords);
    if (dom.recSearch) {
      dom.recSearch.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') loadRecords();
      });
    }

    // Directory
    if (dom.dirSearch) {
      dom.dirSearch.addEventListener('input', () => {
        renderStudentGrid(state.allStudents);
      });
    }

    // Analytics controls
    const defSlider = document.getElementById('defaulter-threshold-slider');
    if (defSlider) {
      defSlider.addEventListener('input', () => {
        const lbl = document.getElementById('defaulter-thresh-label');
        if (lbl) lbl.textContent = `${defSlider.value}%`;
        loadAnalytics();
      });
    }
    const defSub = document.getElementById('defaulter-filter-subject');
    if (defSub) defSub.addEventListener('change', loadAnalytics);
    const defSearch = document.getElementById('defaulter-search-input');
    if (defSearch) defSearch.addEventListener('input', loadAnalytics);
    const btnRefDef = document.getElementById('btn-refresh-defaulters');
    if (btnRefDef) btnRefDef.addEventListener('click', loadAnalytics);

    // Matrix controls
    const btnMatrix = document.getElementById('btn-load-matrix');
    if (btnMatrix) btnMatrix.addEventListener('click', loadMonthlyMatrix);
    const mMonth = document.getElementById('matrix-month');
    if (mMonth) mMonth.addEventListener('change', loadMonthlyMatrix);
    const mYear = document.getElementById('matrix-year');
    if (mYear) mYear.addEventListener('change', loadMonthlyMatrix);
    const mSub = document.getElementById('matrix-subject');
    if (mSub) mSub.addEventListener('change', loadMonthlyMatrix);

    // Profile photo upload inside modal
    const profilePhotoInput = document.getElementById('modal-photo-file-input');
    if (profilePhotoInput) {
      profilePhotoInput.addEventListener('change', async () => {
        const file = profilePhotoInput.files[0];
        if (!file || !activeStudentProfileId) return;

        const formData = new FormData();
        formData.append('photo', file);
        showToast('Uploading new photo and retraining facial encoding...', 'info', 3000);

        try {
          const res = await fetch(`/api/students/${activeStudentProfileId}/photo`, {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || 'Photo update failed');

          showToast('Photo updated and face encoding refreshed!', 'success');
          const avatarImg = document.getElementById('modal-profile-avatar');
          if (avatarImg) {
            avatarImg.src = `${data.photo_url}?t=${Date.now()}`;
            avatarImg.style.display = 'block';
          }
          if (dom.trainedBadge) dom.trainedBadge.textContent = `${data.trained_faces} Enrolled`;
          loadStudents();
          loadDashboard();
        } catch (e) {
          showToast(e.message, 'error');
        } finally {
          profilePhotoInput.value = '';
        }
      });
    }

    // Bulk Import input inside modal
    const modalBulkInput = document.getElementById('modal-bulk-file-input');
    if (modalBulkInput) {
      modalBulkInput.addEventListener('change', () => {
        if (modalBulkInput.files && modalBulkInput.files[0]) {
          handleBulkUploadFile(modalBulkInput.files[0]);
          modalBulkInput.value = '';
        }
      });
    }

    // Subsystems
    setupGroupPhoto();
    setupRegistration();
  }

  // Application Launch
  document.addEventListener('DOMContentLoaded', () => {
    attachEventListeners();
    fetchMeta();
  });

})();
