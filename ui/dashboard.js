function closeDashboard() {
    if (window.pywebview) {
        window.pywebview.api.close_dashboard();
    }
}

function saveSettings() {
    const wakeWord = document.getElementById('wake-word').value;
    const whisperModel = document.getElementById('whisper-model').value;
    const ollamaModel = document.getElementById('ollama-model').value;
    
    if (window.pywebview) {
        window.pywebview.api.save_settings({
            'WAKE_WORD': wakeWord,
            'WAKE_MODEL': whisperModel,
            'OLLAMA_MODEL': ollamaModel
        }).then(() => {
            const status = document.getElementById('save-status');
            status.style.display = 'block';
            setTimeout(() => { status.style.display = 'none'; }, 3000);
        });
    }
}

// Load settings on init
window.addEventListener('pywebviewready', function() {
    window.pywebview.api.get_settings().then(settings => {
        if(settings.WAKE_WORD) document.getElementById('wake-word').value = settings.WAKE_WORD;
        if(settings.WAKE_MODEL) document.getElementById('whisper-model').value = settings.WAKE_MODEL;
        if(settings.OLLAMA_MODEL) document.getElementById('ollama-model').value = settings.OLLAMA_MODEL;
    });
});
