let selectedFiles = [];
let isConverting = false;
let isPaused = false;

document.addEventListener('DOMContentLoaded', function() {
    const selectFilesBtn = document.getElementById('selectFiles');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const startBtn = document.getElementById('startConvert');
    const pauseBtn = document.getElementById('pauseConvert');
    const stopBtn = document.getElementById('stopConvert');
    
    selectFilesBtn.addEventListener('click', async () => {
        // Use HTML file input for now (simpler and more reliable)
        fileInput.click();
    });
    
    fileInput.addEventListener('change', handleFileSelection);
    startBtn.addEventListener('click', startConversion);
    pauseBtn.addEventListener('click', togglePause);
    stopBtn.addEventListener('click', stopConversion);
});

function handleFileSelection(event) {
    const files = Array.from(event.target.files);
    selectedFiles = files.map(file => ({
        name: file.name,
        path: file.path || file.name  // Use file.path if available, otherwise just name
    }));
    
    updateFileList();
    updateButtonStates();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    
    if (selectedFiles.length === 0) {
        fileList.innerHTML = '<p style="color: #999;">尚未選擇檔案</p>';
        return;
    }
    
    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span>${file.name}</span>
            <button class="remove-btn" onclick="removeFile(${index})">移除</button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateButtonStates();
}

function updateButtonStates() {
    const startBtn = document.getElementById('startConvert');
    const pauseBtn = document.getElementById('pauseConvert');
    const stopBtn = document.getElementById('stopConvert');
    
    startBtn.disabled = selectedFiles.length === 0 || isConverting;
    pauseBtn.disabled = !isConverting;
    stopBtn.disabled = !isConverting;
}

async function startConversion() {
    const convertPdf = document.getElementById('convertPdf').checked;
    const convertMd = document.getElementById('convertMd').checked;
    
    if (!convertPdf && !convertMd) {
        addStatusMessage('請至少選擇一種轉換格式', 'error');
        return;
    }
    
    isConverting = true;
    isPaused = false;
    updateButtonStates();
    clearProgress();
    clearStatus();
    
    try {
        const result = await window.pywebview.api.start_conversion({
            files: selectedFiles,
            convert_pdf: convertPdf,
            convert_md: convertMd
        });
        
        if (!result.success && result.error) {
            addStatusMessage(`轉換失敗: ${result.error}`, 'error');
            isConverting = false;
            updateButtonStates();
        }
        // The actual completion will be handled by progress callbacks
    } catch (error) {
        addStatusMessage(`錯誤: ${error.message}`, 'error');
        isConverting = false;
        updateButtonStates();
    }
}

function togglePause() {
    isPaused = !isPaused;
    const pauseBtn = document.getElementById('pauseConvert');
    pauseBtn.textContent = isPaused ? '繼續' : '暫停';
    
    window.pywebview.api.toggle_pause(isPaused);
    addStatusMessage(isPaused ? '轉換已暫停' : '轉換繼續', 'warning');
}

async function stopConversion() {
    if (confirm('確定要中止轉換嗎？')) {
        await window.pywebview.api.stop_conversion();
        isConverting = false;
        isPaused = false;
        updateButtonStates();
        addStatusMessage('轉換已中止', 'error');
    }
}

function updateOverallProgress(current, total) {
    const progressBar = document.getElementById('overallProgress');
    const progressText = document.getElementById('overallProgressText');
    
    const percentage = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.width = percentage + '%';
    progressText.textContent = `${current} / ${total} 檔案`;
}

function updateCurrentProgress(current, total, filename) {
    const progressBar = document.getElementById('currentProgress');
    const progressText = document.getElementById('currentProgressText');
    
    const percentage = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.width = percentage + '%';
    progressText.textContent = `${current} / ${total} 圖片`;
    
    if (filename) {
        addStatusMessage(`正在處理: ${filename}`, 'info');
    }
}

function addStatusMessage(message, type = 'info') {
    const statusLog = document.getElementById('statusLog');
    const timestamp = new Date().toLocaleTimeString('zh-TW');
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message status-${type}`;
    messageDiv.textContent = `[${timestamp}] ${message}`;
    statusLog.appendChild(messageDiv);
    statusLog.scrollTop = statusLog.scrollHeight;
}

function clearProgress() {
    updateOverallProgress(0, 0);
    updateCurrentProgress(0, 0);
}

function clearStatus() {
    document.getElementById('statusLog').innerHTML = '';
}

// pywebview API callbacks
window.addEventListener('pywebviewready', function() {
    // Define the callback function
    window.progressCallback = function(data) {
        if (data.type === 'overall') {
            updateOverallProgress(data.current, data.total);
        } else if (data.type === 'current') {
            updateCurrentProgress(data.current, data.total, data.filename);
        } else if (data.type === 'status') {
            addStatusMessage(data.message, data.level || 'info');
        } else if (data.type === 'complete') {
            addStatusMessage('轉換完成！', 'success');
            addStatusMessage(`報告已儲存至: ${data.report_path}`, 'info');
            isConverting = false;
            updateButtonStates();
        }
    };
    
    // Pass the callback name as a string
    window.pywebview.api.set_progress_callback('progressCallback').then(() => {
        console.log('Progress callback registered');
    });
});