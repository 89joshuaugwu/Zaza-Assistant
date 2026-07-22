function setState(state) {
    const orb = document.getElementById('orb');
    orb.className = `orb ${state}`;
}

function setText(text) {
    const statusText = document.getElementById('status-text');
    statusText.innerText = text;
}

function openDashboard() {
    if (window.pywebview) {
        window.pywebview.api.open_dashboard();
    } else {
        console.log("Dashboard requested (API not available)");
    }
}

// Expose functions to Python
window.setState = setState;
window.setText = setText;
