// Inline Global Handler for Popup Button to ensure 100% reliability
function handlePopupContinue(_0xev) {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    const _0xpopup = document.getElementById("tgPopup");
    const _0xcPlay = document.getElementById("centerPlay");
    const _0xctrls = document.getElementById("controls");
    if (_0xpopup) _0xpopup.style.display = "none";
    if (_0xcPlay) _0xcPlay.classList.remove("hide");
    if (_0xctrls) {
        _0xctrls.classList.remove("hide");
        setTimeout(() => _0xctrls.classList.add("hide"), 3000);
    }
}

;(function(_0x9a8f, _0x21b4) {
    const _0x3e21 = function(_0x51ab) {
        while (--_0x51ab) {
            _0x21b4['push'](_0x21b4['shift']());
        }
    };
    _0x3e21(++_0x21b4);
}(['player', 'video', 'play', 'back', 'fwd', 'fs', 'controls', 'centerPlay', 'progress', 'bar', 'thumb', 'time', 'settings', 'settingsBtn', 'speed', 'quality', 'status', 'dropdownMenu', 'sidebar', 'slideList', 'innerText', 'style', 'display', 'block', 'none', 'active', 'toggle', 'open', 'search', 'get', 'stringify', 'POST', 'application/json', 'ok', 'm3u8Url', 'url', 'notes', 'slides', 'createElement', 'className', 'slide-item', 'innerHTML', 'appendChild', 'currentTime', 'loadSource', 'attachMedia', 'on', 'Events', 'MANIFEST_PARSED', 'levels', 'height', 'LEVEL_SWITCHED', 'ERROR', 'ErrorTypes', 'NETWORK_ERROR', 'startLoad', 'MEDIA_ERROR', 'recoverMediaError', 'destroy', 'canPlayType', 'src', 'addEventListener', 'loadedmetadata', 'duration', 'playbackRate', 'currentLevel', 'requestFullscreen', 'exitFullscreen', 'getBoundingClientRect', 'touches', 'clientX', 'setPointerCapture', 'releasePointerCapture', 'ontimeupdate', 'onloadedmetadata', 'onplay', 'onpause', 'onclick', 'preventDefault', 'stopPropagation', 'paused', 'max', 'min', 'getElementById'], 0x19a));

const _0xgetEl = function(_0xid) {
    return document.getElementById(_0xid);
};

const playerElem = _0xgetEl('player');
const videoElem = _0xgetEl('video');
const playButton = _0xgetEl('play');
const backButton = _0xgetEl('back');
const fwdButton = _0xgetEl('fwd');
const fsButton = _0xgetEl('fs');
const controlsElem = _0xgetEl('controls');
const centerPlayElem = _0xgetEl('centerPlay');
const progressElem = _0xgetEl('progress');
const barElem = _0xgetEl('bar');
const thumbElem = _0xgetEl('thumb');
const tgPopupElem = _0xgetEl('tgPopup');
const timeDisplayElem = _0xgetEl('time');
const settingsElem = _0xgetEl('settings');
const settingsBtnElem = _0xgetEl('settingsBtn');
const speedSelect = _0xgetEl('speed');
const qualitySelect = _0xgetEl('quality');
const statusElem = _0xgetEl('status');
const dropdownMenuElem = _0xgetEl('dropdownMenu');
const sidebarElem = _0xgetEl('sidebar');
const slideListElem = _0xgetEl('slideList');

let isDragging = false, hideTimeoutRef, hlsInstance, wasVideoPlaying = false;
let globalNotesUrl = "";
let globalSlidesArray = [];

function updateStatusText(_0xmsg, _0xtype = 'info') {
    if(!statusElem) return;
    statusElem.innerText = _0xmsg;
    statusElem.style.display = "block";
    if(_0xtype === 'success') {
        setTimeout(() => { statusElem.style.display = 'none'; }, 2500);
    }
}

function toggleMenu(_0xev) {
    _0xev.stopPropagation();
    dropdownMenuElem.classList.toggle('active');
}

function toggleSidebar(_0xev) {
    _0xev.stopPropagation();
    dropdownMenuElem.classList.remove('active');
    sidebarElem.classList.toggle('active');
}

function openNotes(_0xev) {
    _0xev.stopPropagation();
    dropdownMenuElem.classList.remove('active');
    if (globalNotesUrl) {
        window.open(globalNotesUrl, '_blank');
    } else {
        alert('Notes not available for this session.');
    }
}

window.addEventListener('click', () => { 
    if(dropdownMenuElem) dropdownMenuElem.classList.remove('active'); 
});

const urlParamsExtractor = new URLSearchParams(location.search);
const bId = urlParamsExtractor.get("batchId");
const sId = urlParamsExtractor.get("subjectId");
const lId = urlParamsExtractor.get("lectureId");
const directStreamUrl = urlParamsExtractor.get("m3u8Url") || urlParamsExtractor.get("Url");

async function initializePlayerEngine() {
    let resolvedStreamUrl = "";
    
    if (directStreamUrl) {
        resolvedStreamUrl = decodeURIComponent(directStreamUrl);
    } else if (bId && sId && lId) {
        try {
            updateStatusText('🔄 Fetching secure configurations...');
            const endpointRoute = `https://devcoderz-backend.vercel.app/api/config`;
            
            const networkResponse = await fetch(endpointRoute, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ batchId: bId, subjectId: sId, lectureId: lId })
            });

            if (!networkResponse.ok) throw new Error(`Network failure code: ${networkResponse.status}`);
            const responsePayload = await networkResponse.json();
            
            if (responsePayload) {
                resolvedStreamUrl = responsePayload.m3u8Url || responsePayload.url;
                if (responsePayload.notes && responsePayload.notes.length > 0) {
                    globalNotesUrl = responsePayload.notes[0].url;
                }
                if (responsePayload.slides && responsePayload.slides.length > 0) {
                    globalSlidesArray = responsePayload.slides;
                    buildSlideItems();
                }
            }
        } catch (_0xerr) {
            updateStatusText('❌ Error connecting to stream service', 'error');
            return;
        }
    } else {
        updateStatusText('❌ Required parameters missing!', 'error');
        return;
    }

    if (!resolvedStreamUrl) {
        updateStatusText('❌ Target stream source not found!', 'error');
        return;
    }

    setupHlsPlayer(resolvedStreamUrl);
}

function setupHlsPlayer(_0xurl) {
    updateStatusText('🔄 Initializing stream buffer...');

    if (videoElem.canPlayType('application/vnd.apple.mpegurl')) {
        videoElem.src = _0xurl;
        videoElem.addEventListener('loadedmetadata', () => {
            updateStatusText('✅ Playing natively via HLS', 'success');
        });
    } else if (typeof Hls !== 'undefined' && Hls.isSupported()) {
        hlsInstance = new Hls({ 
            enableWorker: true, 
            lowLatencyMode: true,
            maxBufferLength: 30,
            maxMaxBufferLength: 60
        });
        hlsInstance.loadSource(_0xurl);
        hlsInstance.attachMedia(videoElem);

        hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
            updateStatusText('✅ Stream ready!', 'success');
            qualitySelect.innerHTML = '<option value="-1">AUTO</option>';
            hlsInstance.levels.forEach((_0xlvl, _0xidx) => {
                let _0xopt = document.createElement("option");
                _0xopt.value = _0xidx;
                _0xopt.text = _0xlvl.height + "p";
                qualitySelect.appendChild(_0xopt);
            });
        });

        hlsInstance.on(Hls.Events.LEVEL_SWITCHED, (_0xev, _0xdata) => {
            qualitySelect.value = _0xdata.level;
        });

        hlsInstance.on(Hls.Events.ERROR, (_0xev, _0xdata) => {
            if (_0xdata.fatal) {
                switch (_0xdata.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        hlsInstance.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        hlsInstance.recoverMediaError();
                        break;
                    default:
                        hlsInstance.destroy();
                        updateStatusText('❌ Fatal stream error encountered', 'error');
                        break;
                }
            }
        });
    } else {
        updateStatusText('❌ Unsupported browser configuration', 'error');
    }
}

function buildSlideItems() {
    if(!slideListElem) return;
    slideListElem.innerHTML = "";
    globalSlidesArray.forEach((_0xslide) => {
        const _0xcard = document.createElement('div');
        _0xcard.className = 'slide-item';
        const _0xtimeStr = formatTimestamp(_0xslide.timestamp);
        
        _0xcard.innerHTML = `
            <img src="${_0xslide.image}" alt="Slide">
            <div class="slide-time">🕒 ${_0xtimeStr}</div>
        `;
        _0xcard.onclick = (_0xev) => {
            _0xev.stopPropagation();
            videoElem.currentTime = _0xslide.timestamp;
            videoElem.play();
            if(window.innerWidth < 600) sidebarElem.classList.remove('active');
        };
        slideListElem.appendChild(_0xcard);
    });
}

window.addEventListener('load', () => {
    setTimeout(initializePlayerEngine, 400);
});

function formatTimestamp(_0xsec) {
    if(!_0xsec || isNaN(_0xsec) || _0xsec === Infinity) return "00:00:00";
    let _0xh = Math.floor(_0xsec / 3600);
    let _0xm = Math.floor((_0xsec % 3600) / 60);
    let _0xs = Math.floor(_0xsec % 60);
    return [_0xh, _0xm, _0xs].map(_0xnum => String(_0xnum).padStart(2, "0")).join(":");
}

function refreshProgressBarUI(_0xpct, _0xcurr, _0xdur) {
    if(!barElem || !thumbElem || !timeDisplayElem) return;
    barElem.style.width = _0xpct + "%";
    thumbElem.style.left = _0xpct + "%";
    timeDisplayElem.innerText = `${formatTimestamp(_0xcurr)} / ${formatTimestamp(_0xdur)}`;
}

function triggerSafePlayback() {
    videoElem.play().catch(() => {
        videoElem.muted = true;
        videoElem.play();
    });
}

function handleControlVisibility(_0xpermanent = false) {
    if(!controlsElem) return;
    controlsElem.classList.remove("hide");
    clearTimeout(hideTimeoutRef);
    if(!_0xpermanent) {
        hideTimeoutRef = setTimeout(() => controlsElem.classList.add("hide"), 3000);
    }
}

centerPlayElem.onclick = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    triggerSafePlayback();
};

playButton.onclick = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    videoElem.paused ? triggerSafePlayback() : videoElem.pause();
};

backButton.onclick = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    videoElem.currentTime = Math.max(0, videoElem.currentTime - 10);
    handleControlVisibility(true);
};

fwdButton.onclick = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    videoElem.currentTime = Math.min(videoElem.duration, videoElem.currentTime + 10);
    handleControlVisibility(true);
};

settingsBtnElem.onclick = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    settingsElem.style.display = (settingsElem.style.display === "block" ? "none" : "block");
    handleControlVisibility(true);
};

speedSelect.onchange = () => {
    videoElem.playbackRate = parseFloat(speedSelect.value);
};

qualitySelect.onchange = () => {
    if(hlsInstance) hlsInstance.currentLevel = parseInt(qualitySelect.value);
};

fsButton.onclick = async _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    try {
        if (!document.fullscreenElement) {
            await playerElem.requestFullscreen();
            if (screen.orientation && screen.orientation.lock) {
                await screen.orientation.lock('landscape').catch(() => {});
            }
        } else {
            if (screen.orientation && screen.orientation.unlock) {
                screen.orientation.unlock();
            }
            await document.exitFullscreen();
        }
    } catch (_0xerr) {}
};

function extractPointerPosition(_0xev) {
    const _0xrect = progressElem.getBoundingClientRect();
    const _0xclientX = _0xev.touches ? _0xev.touches[0].clientX : _0xev.clientX;
    let _0xcalcPos = (_0xclientX - _0xrect.left) / _0xrect.width;
    return Math.max(0, Math.min(1, _0xcalcPos));
}

progressElem.onpointerdown = _0xev => {
    _0xev.preventDefault();
    _0xev.stopPropagation();
    isDragging = true;
    wasVideoPlaying = !videoElem.paused;
    videoElem.pause();
    progressElem.setPointerCapture(_0xev.pointerId);
    let _0xpos = extractPointerPosition(_0xev);
    if(videoElem.duration) {
        videoElem.currentTime = _0xpos * videoElem.duration;
        refreshProgressBarUI(_0xpos * 100, videoElem.currentTime, videoElem.duration);
    }
};

progressElem.onpointermove = _0xev => {
    if(!isDragging) return;
    _0xev.preventDefault();
    _0xev.stopPropagation();
    let _0xpos = extractPointerPosition(_0xev);
    if(videoElem.duration) {
        videoElem.currentTime = _0xpos * videoElem.duration;
        refreshProgressBarUI(_0xpos * 100, videoElem.currentTime, videoElem.duration);
    }
};

progressElem.onpointerup = _0xev => {
    if(!isDragging) return;
    _0xev.preventDefault();
    _0xev.stopPropagation();
    isDragging = false;
    try { progressElem.releasePointerCapture(_0xev.pointerId); } catch(_0xerr) {}
    if(wasVideoPlaying) { triggerSafePlayback(); }
};

videoElem.ontimeupdate = () => {
    if(!isDragging && videoElem.duration) {
        refreshProgressBarUI((videoElem.currentTime / videoElem.duration) * 100, videoElem.currentTime, videoElem.duration);
    }
};

videoElem.onloadedmetadata = () => {
    if(videoElem.duration) {
        refreshProgressBarUI(0, videoElem.currentTime, videoElem.duration);
    }
};

videoElem.onplay = () => {
    playButton.classList.add("pause");
    centerPlayElem.classList.add("hide");
    handleControlVisibility();
};

videoElem.onpause = () => {
    playButton.classList.remove("pause");
    centerPlayElem.classList.add("hide");
    handleControlVisibility(true);
};

playerElem.onclick = _0xev => {
    if(tgPopupElem.style.display !== "none") return;
    if(_0xev.target === videoElem || _0xev.target === playerElem) {
        sidebarElem.classList.remove('active');
        if(controlsElem.classList.contains("hide")) {
            handleControlVisibility();
        } else {
            controlsElem.classList.add("hide");
            settingsElem.style.display = "none";
        }
    }
};
