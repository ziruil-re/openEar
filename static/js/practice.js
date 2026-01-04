// 练习页面JavaScript

// 侧边栏收起/展开功能
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    // 侧边栏拖拽调整宽度功能
    const sidebarResizer = document.getElementById('sidebar-resizer');
    if (sidebarResizer && sidebar) {
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        
        // 从localStorage恢复宽度
        const savedWidth = localStorage.getItem('sidebar-width');
        if (savedWidth) {
            sidebar.style.width = savedWidth + 'px';
        }
        
        sidebarResizer.addEventListener('mousedown', function(e) {
            isResizing = true;
            startX = e.clientX;
            startWidth = sidebar.offsetWidth;
            sidebarResizer.classList.add('dragging');
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isResizing) return;
            
            const diff = startX - e.clientX; // 因为是左侧调整，所以用减法
            const newWidth = startWidth + diff;
            const minWidth = 280;
            const maxWidth = 700;
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                sidebar.style.width = newWidth + 'px';
                // 保存到localStorage
                localStorage.setItem('sidebar-width', newWidth);
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isResizing) {
                isResizing = false;
                sidebarResizer.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }
});

// 修复AI秘籍下拉框宽度
function fixAISelectWidth() {
    const explanationTab = document.getElementById('explanation-tab');
    if (!explanationTab || !explanationTab.classList.contains('active')) {
        return; // tab没有显示，不处理
    }
    
    const scaleSelect = document.getElementById('scale-select-ai');
    const intervalSelect = document.getElementById('interval-select-ai');
    const chordSelect = document.getElementById('chord-select-ai');
    const select = scaleSelect || intervalSelect || chordSelect;
    
    if (!select) {
        return;
    }
    
    const sidebar = document.querySelector('.sidebar');
    const sidebarContent = document.querySelector('.sidebar-content');
    
    if (!sidebar || !sidebarContent) {
        return;
    }
    
    // 获取sidebar的实际宽度
    const sidebarWidth = sidebar.offsetWidth;
    const sidebarContentPadding = 
        (parseInt(window.getComputedStyle(sidebarContent).paddingLeft) || 0) + 
        (parseInt(window.getComputedStyle(sidebarContent).paddingRight) || 0);
    
    const expectedWidth = sidebarWidth - sidebarContentPadding;
    
    // 如果宽度为0或不足，强制修复
    if (select.offsetWidth === 0 || select.offsetWidth < expectedWidth - 10) {
        // 强制设置所有相关元素的宽度
        const parent = select.parentElement;
        if (parent && parent.classList.contains('ai-secret-select-group')) {
            parent.style.setProperty('width', '100%', 'important');
            parent.style.setProperty('max-width', '100%', 'important');
            parent.style.setProperty('box-sizing', 'border-box', 'important');
        }
        
        // 设置下拉框宽度
        if (expectedWidth > 0) {
            select.style.setProperty('width', expectedWidth + 'px', 'important');
            select.style.setProperty('max-width', expectedWidth + 'px', 'important');
        } else {
            select.style.setProperty('width', '100%', 'important');
            select.style.setProperty('max-width', '100%', 'important');
        }
        select.style.setProperty('min-width', '0', 'important');
        select.style.setProperty('box-sizing', 'border-box', 'important');
        select.style.setProperty('display', 'block', 'important');
    }
}

// 标签页切换
document.querySelectorAll('.sidebar-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        // 更新标签页状态
        document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // 如果切换到AI秘籍tab，修复下拉框宽度
        if (tabName === 'explanation') {
            setTimeout(fixAISelectWidth, 100);
        }
    });
});

// 页面加载完成后修复
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(fixAISelectWidth, 200);
});

// 监听窗口大小变化
window.addEventListener('resize', () => {
    setTimeout(fixAISelectWidth, 100);
});

// 全选音程
const selectAllIntervals = document.getElementById('select-all-intervals');
if (selectAllIntervals) {
    selectAllIntervals.addEventListener('change', (e) => {
        document.querySelectorAll('input[name="intervals"]').forEach(cb => {
            if (cb.id !== 'select-all-intervals') {
                cb.checked = e.target.checked;
            }
        });
    });
}

// 全选和弦类型
const selectAllChords = document.getElementById('select-all-chords');
if (selectAllChords) {
    selectAllChords.addEventListener('change', (e) => {
        document.querySelectorAll('input[name="chord_types"]').forEach(cb => {
            if (cb.id !== 'select-all-chords') {
                cb.checked = e.target.checked;
            }
        });
    });
}

// 全选罗马数字
const selectAllRoman = document.getElementById('select-all-roman');
if (selectAllRoman) {
    selectAllRoman.addEventListener('change', (e) => {
        document.querySelectorAll('input[name="roman_numerals"]').forEach(cb => {
            if (cb.id !== 'select-all-roman') {
                cb.checked = e.target.checked;
            }
        });
    });
}

// 应用设置
function applySettings() {
    const form = document.getElementById('settings-form');
    const formData = new FormData(form);
    const exerciseType = window.location.pathname.split('/').pop();
    window.exerciseType = exerciseType;
    
    const settings = {
        total_questions: formData.get('total_questions')
    };
    
    // 更新总题目数
    totalQuestions = parseInt(settings.total_questions) || 20;
    // 重置统计
    currentScore = 0;
    currentTotal = 0;
    
    if (exerciseType === 'interval') {
        settings.intervals = formData.getAll('intervals');
        settings.directions = formData.getAll('directions');
    } else if (exerciseType === 'scale_degree') {
        settings.scale_type = formData.get('scale_type');
        settings.key = formData.get('key');
        settings.octave = formData.get('octave');
        settings.octave_range = formData.get('octave_range');
        } else if (exerciseType === 'chord_quality') {
            settings.roots = formData.getAll('roots');
            settings.chord_types = formData.getAll('chord_types');
    }
    
    // 保存到sessionStorage
    sessionStorage.setItem('practice_settings', JSON.stringify(settings));
    window.currentSettings = settings;
    
    // 结束当前会话（如果存在）
    if (currentSessionId) {
        endCurrentSession();
    }
    
    // 开始新会话
    startNewSession();
    
    // 重新加载题目
    loadQuestion();
    
    alert('设置已应用！');
}

// 开始新会话
function startNewSession() {
    // 检查用户是否已登录（通过检查导航栏中是否有用户名）
    const navUser = document.querySelector('.nav-user');
    const isAuthenticated = navUser !== null;
    
    if (!isAuthenticated) {
        return; // 未登录用户不记录会话
    }
    
    const exerciseType = window.location.pathname.split('/').pop();
    const settings = JSON.parse(sessionStorage.getItem('practice_settings') || '{}');
    
    fetch('/api/start_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            exercise_type: exerciseType,
            settings: settings
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            currentSessionId = data.session_id;
            sessionStartTime = Date.now();
        }
    })
    .catch(error => {
        console.error('开始会话失败:', error);
    });
}

// 结束当前会话
function endCurrentSession() {
    if (!currentSessionId) {
        return;
    }
    
    const duration = sessionStartTime ? Math.floor((Date.now() - sessionStartTime) / 1000) : 0;
    
    fetch('/api/end_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: currentSessionId,
            duration: duration,
            total_questions: currentTotal,
            correct_answers: currentScore
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            currentSessionId = null;
            sessionStartTime = null;
        }
    })
    .catch(error => {
        console.error('结束会话失败:', error);
    });
}

// 加载题目
function loadQuestion() {
    const questionArea = document.getElementById('question-area');
    questionArea.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>正在加载题目...</p>
        </div>
    `;
    
    // 获取设置
    const settings = JSON.parse(sessionStorage.getItem('practice_settings') || '{}');
    window.currentSettings = settings;
    
    // 获取当前练习类型
    const exerciseType = window.location.pathname.split('/').pop();
    window.exerciseType = exerciseType;
    
    // 构建请求参数
    const params = new URLSearchParams();
    if (exerciseType === 'interval') {
        const intervals = settings.intervals || [];
        const directions = settings.directions || ['up', 'down'];
        if (intervals.length > 0) {
            params.append('intervals', intervals.join(','));
        }
        if (directions.length > 0) {
            params.append('directions', directions.join(','));
        }
    } else if (exerciseType === 'scale_degree') {
        if (settings.scale_type) {
            params.append('scale_type', settings.scale_type);
        }
        if (settings.key) {
            params.append('key', settings.key);
        }
        if (settings.octave) {
            params.append('octave', settings.octave);
        }
        if (settings.octave_range) {
            params.append('octave_range', settings.octave_range);
        }
    } else if (exerciseType === 'chord_quality') {
        if (settings.roots && settings.roots.length > 0) {
            params.append('roots', settings.roots.join(','));
        }
        if (settings.chord_types && settings.chord_types.length > 0) {
            params.append('chord_types', settings.chord_types.join(','));
        }
    }
    
    // 调用API获取题目
    fetch(`/api/generate_question/${exerciseType}?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                displayQuestion(data);
            } else {
                questionArea.innerHTML = `<div class="error-message">${data.msg || '加载失败'}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            questionArea.innerHTML = '<div class="error-message">加载失败，请刷新页面重试</div>';
        });
}

// 显示题目
function displayQuestion(data) {
    window.currentQuestion = data;
    // 确保scale_audio_file被存储（用于音阶练习）
    if (data.scale_audio_file) {
        window.currentQuestion.scale_audio_file = data.scale_audio_file;
        console.log(`📊 完整音阶音频文件: ${data.scale_audio_file}`);
    }
    // 记录题目开始时间
    questionStartTime = Date.now();
    const questionArea = document.getElementById('question-area');
    const answersLayout = document.getElementById('answers-layout');
    const exerciseType = window.exerciseType;
    
    let questionHtml = '';
    let answersHtml = '';
    
    // 获取进度文本
    const progressText = getProgressText();
    
    if (exerciseType === 'interval') {
        // 显示音符信息：C5-?（初始不显示答案）
        const note1 = data.note1 || '';
        const note2Display = '?'; // 初始总是显示?
        const noteDisplay = note1 ? `${note1}-${note2Display}` : '';
        
        questionHtml = `
            <div class="audio-player-container">
                <h3 style="font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600; color: #000000; margin-bottom: 8px; text-align: left;">🎧 请听音程，选择正确的音程名称： ${progressText}</h3>
                ${noteDisplay ? `
                <p style="font-size: 13px; color: #606060; margin-bottom: 8px; font-family: 'JetBrains Mono', 'Space Mono', monospace; text-align: left;">
                    现在播放的音符是：<strong style="color: #000000;" id="interval-note-display">${noteDisplay}</strong>
                </p>
                ` : ''}
                <div id="interval-audio-container">
                    <audio id="audioPlayer" controls preload="metadata">
                        <source src="/static/audio/${data.audio_file}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <br>
                    <button class="play-audio-btn" onclick="playAudio()">
                        <span>▶️</span> 播放音程
                    </button>
                </div>
            </div>
        `;
        
        // 存储音符信息用于显示正确答案
        window.intervalNote1 = note1;
        window.intervalNote2 = data.note2;
        answersHtml = `
            <div class="answers-layout-rows-container">
                <div class="answers-layout-row">
                    ${data.options.map((option, index) => `
                        <button class="answer-button" data-value="${data.option_values[index]}" onclick="selectAnswer('${data.option_values[index]}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    } else if (exerciseType === 'scale_degree') {
        questionHtml = `
            <div class="audio-player-container">
                <h3 style="font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600; color: #000000; margin-bottom: 8px; text-align: left;">🎧 请听音符，选择它在音阶中的音级： ${progressText}</h3>
                <p style="font-size: 13px; color: #606060; margin-bottom: 8px; font-family: 'JetBrains Mono', 'Space Mono', monospace; text-align: left;">
                    当前音阶：<strong style="color: #000000;">${data.scale_name || ''}</strong>
                </p>
                <audio id="audioPlayer" controls preload="metadata">
                    <source src="/static/audio/${data.audio_file}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
                <br>
                <button class="play-audio-btn" onclick="playAudio()">
                    <span>▶️</span> 播放题目音频
                </button>
            </div>
            <div class="reference-audio-container" style="margin-top: 12px;">
                <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #000000; font-family: 'JetBrains Mono', 'Space Mono', monospace;">参考音频：</h4>
                <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                    ${data.root_audio_file ? `
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 11px; color: #606060; margin-bottom: 4px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">根音：</label>
                        <audio controls preload="metadata" style="width: 100%;" onerror="console.error('根音音频加载失败:', this.src)">
                            <source src="/static/audio/${data.root_audio_file}" type="audio/mpeg">
                            您的浏览器不支持音频播放。
                        </audio>
                    </div>
                    ` : `
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 11px; color: #606060; margin-bottom: 4px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">根音：</label>
                        <p style="font-size: 11px; color: #dc2626; padding: 8px; background: #fee2e2; border-radius: 4px;">⚠️ 根音音频未加载</p>
                    </div>
                    `}
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 11px; color: #606060; margin-bottom: 4px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">完整音阶：</label>
                        ${data.scale_audio_file ? `
                        <audio id="scaleAudioPlayer" controls preload="metadata" style="width: 100%;" onerror="console.error('音阶音频加载失败:', this.src)">
                            <source src="/static/audio/${data.scale_audio_file}" type="audio/mpeg">
                            您的浏览器不支持音频播放。
                        </audio>
                        ` : '<p style="font-size: 11px; color: #dc2626; padding: 8px; background: #fee2e2; border-radius: 4px;">⚠️ 音阶音频未加载</p>'}
                    </div>
                </div>
            </div>
        `;
        answersHtml = `
            <div class="answers-layout-rows-container">
                <div class="answers-layout-row">
                    ${data.options.map((option) => `
                        <button class="answer-button" data-value="${option}" onclick="selectAnswer('${option}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    } else if (exerciseType === 'chord_quality') {
        // 初始显示根音和问号，选完答案后再显示正确的和弦音符
        const rootNote = data.root_note || '';
        const chordNotes = data.chord_notes || [];
        // 计算需要显示的问号数量（除了根音外的其他音符）
        let initialNoteDisplay = '?';
        if (rootNote && chordNotes.length > 1) {
            // 有根音且和弦有多个音符，显示"根音-？-？"
            const questionMarks = Array(chordNotes.length - 1).fill('?').join('-');
            initialNoteDisplay = `${rootNote}-${questionMarks}`;
        } else if (rootNote) {
            // 只有根音，直接显示根音
            initialNoteDisplay = rootNote;
        } else if (chordNotes.length > 0) {
            // 没有根音但有和弦音符，显示问号
            const questionMarks = Array(chordNotes.length).fill('?').join('-');
            initialNoteDisplay = questionMarks;
        }
        
        questionHtml = `
            <div class="audio-player-container">
                <h3 style="font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600; color: #000000; margin-bottom: 8px; text-align: left;">🎧 请听和弦，选择正确的和弦类型： ${progressText}</h3>
                <p style="font-size: 13px; color: #606060; margin-bottom: 8px; font-family: 'JetBrains Mono', 'Space Mono', monospace; text-align: left;">
                    根音：<strong style="color: #000000;">${data.root_note || ''}</strong>
                </p>
                <div id="chord-audio-container">
                    <p style="font-size: 12px; color: #606060; margin-bottom: 8px; font-family: 'JetBrains Mono', 'Space Mono', monospace;">
                        和弦音符：<strong style="color: #000000;" id="chord-notes-display">${initialNoteDisplay}</strong>
                    </p>
                    <button class="play-audio-btn" onclick="playChordAudio()">
                        <span>▶️</span> 播放和弦
                    </button>
                </div>
                ${data.root_audio_file ? `
                <div style="margin-top: 12px;">
                    <label style="font-size: 12px; color: #606060; margin-bottom: 6px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">参考根音：</label>
                    <audio controls preload="metadata" style="width: 100%;">
                        <source src="/static/audio/${data.root_audio_file}" type="audio/mpeg">
                    </audio>
                </div>
                ` : ''}
            </div>
        `;
        
        // 存储和弦音符信息用于显示正确答案
        window.chordNotes = chordNotes;
        answersHtml = `
            <div class="answers-layout-rows-container">
                <div class="answers-layout-row">
                    ${data.options.map((option, index) => `
                        <button class="answer-button" data-value="${data.option_values[index]}" onclick="selectAnswer('${data.option_values[index]}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        // 存储和弦音频文件（单个文件）
        window.chordAudioFile = data.chord_audio_file || null;
    }
    
    questionArea.innerHTML = questionHtml;
    
    // 将答案按钮插入到answers-layout中（操作按钮之前）
    if (answersLayout) {
        const actionsContainer = answersLayout.querySelector('.exercise-actions-container');
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = answersHtml;
        const answersContainer = tempDiv.firstElementChild;
        
        if (actionsContainer) {
            // 清除旧的答案按钮
            const oldAnswers = answersLayout.querySelector('.answers-layout-rows-container');
            if (oldAnswers) {
                oldAnswers.remove();
            }
            // 在操作按钮之前插入新的答案按钮
            answersLayout.insertBefore(answersContainer, actionsContainer);
        } else {
            // 如果没有操作按钮容器，直接替换内容
            answersLayout.innerHTML = answersHtml;
        }
    }
    
    // 重置按钮状态和颜色
    const btnRepeat = document.getElementById('btn-repeat');
    const btnNext = document.getElementById('btn-next');
    if (btnRepeat) btnRepeat.disabled = false;
    if (btnNext) btnNext.disabled = true;
    
    // 重置所有答案按钮的颜色
    document.querySelectorAll('.answer-button, .option-btn').forEach(btn => {
        btn.style.backgroundColor = '';
        btn.style.color = '';
        btn.style.borderColor = '';
        btn.disabled = false;
    });
}

// 选择答案
function selectAnswer(answer) {
    if (!window.currentQuestion) return;
    
    window.selectedAnswer = answer;
    
    // 禁用所有选项（但先不改变颜色，等showResult再改）
    document.querySelectorAll('.answer-button, .option-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // 计算响应时间
    const responseTime = questionStartTime ? (Date.now() - questionStartTime) / 1000 : 0;
    
    // 准备题目数据
    const questionData = {
        exercise_type: window.exerciseType,
        note1: window.currentQuestion.note1,
        note2: window.currentQuestion.note2,
        audio_file: window.currentQuestion.audio_file,
        scale_name: window.currentQuestion.scale_name,
        root_note: window.currentQuestion.root_note
    };
    
    // 提交答案到后端
    fetch('/api/submit_answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            answer: answer,
            correct_value: window.currentQuestion.correct_value,
            session_id: currentSessionId,
            question_data: questionData,
            response_time: responseTime,
            sub_item: window.currentQuestion.sub_item || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            showResult(data);
            updateStats(data.is_correct);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 更新统计
let currentScore = 0;
let currentTotal = 0;
let totalQuestions = 20; // 默认题目数量
let currentSessionId = null; // 当前会话ID
let sessionStartTime = null; // 会话开始时间
let questionStartTime = null; // 题目开始时间

// 获取进度和准确率文本
function getProgressText() {
    const accuracy = currentTotal > 0 ? Math.round((currentScore / currentTotal) * 100) : 0;
    return `${currentTotal}/${totalQuestions} (${accuracy}%)`;
}

// 更新题目标题中的进度信息
function updateQuestionTitle() {
    const progressText = getProgressText();
    const questionTitle = document.querySelector('.audio-player-container h3');
    if (questionTitle) {
        // 移除旧的进度信息（如果存在）
        let titleText = questionTitle.textContent.replace(/\s+\d+\/\d+\s*\(\d+%\)/, '');
        // 添加新的进度信息
        questionTitle.textContent = titleText + ' ' + progressText;
    }
}

function updateStats(isCorrect) {
    currentTotal++;
    if (isCorrect) {
        currentScore++;
    }
    
    updateQuestionTitle();
}

// 显示结果
function showResult(data) {
    // 如果是音程练习，更新音符显示（将?替换为正确的note2）
    if (window.exerciseType === 'interval' && window.intervalNote2) {
        const noteDisplay = document.getElementById('interval-note-display');
        if (noteDisplay) {
            const note1 = window.intervalNote1 || '';
            noteDisplay.textContent = `${note1}-${window.intervalNote2}`;
        }
    }
    
    // 如果是和弦练习，更新和弦音符显示（将?替换为正确的音符）
    if (window.exerciseType === 'chord_quality' && window.chordNotes && window.chordNotes.length > 0) {
        const chordNotesDisplay = document.getElementById('chord-notes-display');
        if (chordNotesDisplay) {
            // 使用 - 连接，与初始显示格式一致
            chordNotesDisplay.textContent = window.chordNotes.join('-');
        }
    }
    
    // 标记正确答案和错误答案（使用颜色）
    const selectedAnswer = window.selectedAnswer || '';
    const correctValue = data.correct_value || data.correct_answer;
    
    document.querySelectorAll('.answer-button, .option-btn').forEach(btn => {
        btn.disabled = true;
        const btnText = btn.textContent.trim();
        const btnValue = btn.getAttribute('data-value') || btnText;
        
        // 检查是否是正确答案（匹配文本或值）
        const isCorrectAnswer = btnText === data.correct_answer || btnValue === correctValue || btnValue === data.correct_answer;
        // 检查是否是用户选择的答案
        const isUserAnswer = btnText === selectedAnswer || btnValue === selectedAnswer;
        
        if (isCorrectAnswer) {
            // 正确答案：绿色
            btn.style.backgroundColor = '#10b981';
            btn.style.color = '#ffffff';
            btn.style.borderColor = '#10b981';
        } else if (isUserAnswer && !data.is_correct) {
            // 用户选择的错误答案：红色
            btn.style.backgroundColor = '#ef4444';
            btn.style.color = '#ffffff';
            btn.style.borderColor = '#ef4444';
        }
    });
    
    // 启用下一题按钮
    const btnNext = document.getElementById('btn-next');
    if (btnNext) {
        btnNext.disabled = false;
    }
}

// 播放音频函数
function playAudio() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (audioPlayer) {
        // 移动端需要先加载音频
        if (audioPlayer.readyState === 0) {
            audioPlayer.load();
        }
        
        // 等待音频可以播放
        const playPromise = audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise.catch(e => {
                console.error('播放失败:', e);
                // 移动端可能需要用户交互，尝试重新加载
                if (e.name === 'NotAllowedError' || e.name === 'NotSupportedError') {
                    audioPlayer.load();
                }
            });
        }
    }
}

// 播放完整音阶音频（已拼接好的8个音符，每个0.5秒，总共4秒）

// 重复播放音频
function repeatAudio() {
    const audioPlayer = document.getElementById('audioPlayer');
    if (audioPlayer) {
        audioPlayer.currentTime = 0;
        audioPlayer.play().catch(e => {
            console.error('播放失败:', e);
        });
    }
}

// 播放和弦音频（单个文件）
function playChordAudio() {
    if (!window.chordAudioFile) {
        console.error('没有和弦音频文件');
        return;
    }
    
    // 停止之前播放的音频
    if (window.chordAudioPlayer) {
        window.chordAudioPlayer.pause();
        window.chordAudioPlayer.currentTime = 0;
    }
    
    // 创建新的音频播放器
    const audio = new Audio(`/static/audio/${window.chordAudioFile}`);
    window.chordAudioPlayer = audio;
    
    audio.play().catch(e => {
        console.error('播放和弦音频失败:', e);
    });
}

// 下一题
function nextQuestion() {
    loadQuestion();
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 获取当前练习类型
    const exerciseType = window.location.pathname.split('/').pop();
    window.exerciseType = exerciseType;
    
    // 初始化默认设置（如果还没有设置）
    if (!sessionStorage.getItem('practice_settings')) {
        let defaultSettings = {
            total_questions: '20'
        };
        
        if (exerciseType === 'interval') {
            const checkedIntervals = Array.from(document.querySelectorAll('input[name="intervals"]:checked')).map(cb => cb.value);
            const checkedDirections = Array.from(document.querySelectorAll('input[name="directions"]:checked')).map(cb => cb.value);
            defaultSettings.intervals = checkedIntervals.length > 0 ? checkedIntervals : ['minor_second', 'major_second', 'minor_third', 'major_third', 'perfect_fourth', 'perfect_fifth'];
            defaultSettings.directions = checkedDirections.length > 0 ? checkedDirections : ['up', 'down'];
        } else if (exerciseType === 'scale_degree') {
            const scaleType = document.querySelector('select[name="scale_type"]')?.value || 'major';
            const key = document.querySelector('select[name="key"]')?.value || 'C';
            const octave = document.querySelector('select[name="octave"]')?.value || '4';
            const octaveRange = document.querySelector('select[name="octave_range"]')?.value || '1';
            defaultSettings.scale_type = scaleType;
            defaultSettings.key = key;
            defaultSettings.octave = octave;
            defaultSettings.octave_range = octaveRange;
        } else if (exerciseType === 'chord_quality') {
            const allRoots = Array.from(document.querySelectorAll('input[name="roots"]')).map(cb => cb.value);
            const checkedRoots = Array.from(document.querySelectorAll('input[name="roots"]:checked')).map(cb => cb.value);
            const checkedChordTypes = Array.from(document.querySelectorAll('input[name="chord_types"]:checked')).map(cb => cb.value);
            // 默认全选所有根音
            defaultSettings.roots = checkedRoots.length > 0 ? checkedRoots : allRoots;
            defaultSettings.chord_types = checkedChordTypes.length > 0 ? checkedChordTypes : ['major', 'minor'];
        }
        
        sessionStorage.setItem('practice_settings', JSON.stringify(defaultSettings));
    } else {
        // 如果已有设置，但缺少某些字段，补充默认值
        const settings = JSON.parse(sessionStorage.getItem('practice_settings') || '{}');
        let needUpdate = false;
        
        if (exerciseType === 'chord_quality') {
            // 如果没有roots字段，从表单中读取或使用默认值
            if (!settings.roots || settings.roots.length === 0) {
                const checkedRoots = Array.from(document.querySelectorAll('input[name="roots"]:checked')).map(cb => cb.value);
                settings.roots = checkedRoots.length > 0 ? checkedRoots : ['C'];
                needUpdate = true;
            }
            // 如果没有chord_types字段，从表单中读取或使用默认值
            if (!settings.chord_types || settings.chord_types.length === 0) {
                const checkedChordTypes = Array.from(document.querySelectorAll('input[name="chord_types"]:checked')).map(cb => cb.value);
                settings.chord_types = checkedChordTypes.length > 0 ? checkedChordTypes : ['major', 'minor'];
                needUpdate = true;
            }
        }
        
        if (needUpdate) {
            sessionStorage.setItem('practice_settings', JSON.stringify(settings));
        }
    }
    
    // 初始化题目数量
    const settings = JSON.parse(sessionStorage.getItem('practice_settings') || '{}');
    totalQuestions = parseInt(settings.total_questions) || 20;
    currentScore = 0;
    currentTotal = 0;
    
    // 绑定按钮事件
    const btnRepeat = document.getElementById('btn-repeat');
    const btnNext = document.getElementById('btn-next');
    if (btnRepeat) {
        btnRepeat.addEventListener('click', repeatAudio);
    }
    if (btnNext) {
        btnNext.addEventListener('click', nextQuestion);
    }
    
    // 开始新会话
    startNewSession();
    
    loadQuestion();
    
    // 页面卸载时结束会话
    window.addEventListener('beforeunload', () => {
        endCurrentSession();
    });
});

