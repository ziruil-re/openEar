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
});

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
    });
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

// 应用设置
function applySettings() {
    const form = document.getElementById('settings-form');
    const formData = new FormData(form);
    const exerciseType = window.location.pathname.split('/').pop();
    window.exerciseType = exerciseType;
    
    const settings = {
        total_questions: formData.get('total_questions')
    };
    
    if (exerciseType === 'interval') {
        settings.intervals = formData.getAll('intervals');
        settings.directions = formData.getAll('directions');
    } else if (exerciseType === 'scale_degree') {
        settings.scale_type = formData.get('scale_type');
        settings.key = formData.get('key');
        settings.octave = formData.get('octave');
        settings.octave_range = formData.get('octave_range');
    }
    
    // 保存到sessionStorage
    sessionStorage.setItem('practice_settings', JSON.stringify(settings));
    window.currentSettings = settings;
    
    // 重新加载题目
    loadQuestion();
    
    alert('设置已应用！');
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
    const questionArea = document.getElementById('question-area');
    const answersLayout = document.getElementById('answers-layout');
    const exerciseType = window.exerciseType;
    
    let questionHtml = '';
    let answersHtml = '';
    
    if (exerciseType === 'interval') {
        questionHtml = `
            <div class="audio-player-container">
                <h3>🎧 请听音程，选择正确的音程名称：</h3>
                <audio id="audioPlayer" controls preload="auto">
                    <source src="/static/audio/${data.audio_file}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
                <br>
                <button class="play-audio-btn" onclick="playAudio()">
                    <span>▶️</span> 播放音频
                </button>
            </div>
        `;
        answersHtml = `
            <div class="answers-layout-rows-container">
                <div class="answers-layout-row">
                    ${data.options.map((option, index) => `
                        <button class="answer-button" onclick="selectAnswer('${data.option_values[index]}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    } else if (exerciseType === 'scale_degree') {
        questionHtml = `
            <div class="audio-player-container">
                <h3 style="font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600; color: #000000; margin-bottom: 12px;">🎧 请听音符，选择它在音阶中的音级：</h3>
                <p style="font-size: 13px; color: #606060; margin-bottom: 12px; font-family: 'JetBrains Mono', 'Space Mono', monospace;">
                    当前音阶：<strong style="color: #000000;">${data.scale_name || ''}</strong>
                </p>
                <audio id="audioPlayer" controls preload="auto">
                    <source src="/static/audio/${data.audio_file}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
                <br>
                <button class="play-audio-btn" onclick="playAudio()">
                    <span>▶️</span> 播放题目音频
                </button>
            </div>
            <div class="reference-audio-container">
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #000000; font-family: 'JetBrains Mono', 'Space Mono', monospace;">参考音频：</h4>
                <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 12px; color: #606060; margin-bottom: 6px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">根音：</label>
                        <audio controls preload="auto" style="width: 100%;">
                            <source src="/static/audio/${data.root_audio_file}" type="audio/wav">
                        </audio>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 12px; color: #606060; margin-bottom: 6px; display: block; font-family: 'JetBrains Mono', 'Space Mono', monospace; font-weight: 600;">完整音阶：</label>
                        <audio controls preload="auto" style="width: 100%;">
                            <source src="/static/audio/${data.scale_audio_file}" type="audio/wav">
                        </audio>
                    </div>
                </div>
            </div>
        `;
        answersHtml = `
            <div class="answers-layout-rows-container">
                <div class="answers-layout-row">
                    ${data.options.map((option) => `
                        <button class="answer-button" onclick="selectAnswer('${option}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    questionArea.innerHTML = questionHtml + '<div id="result-message" class="result-message" style="display: none;"></div>';
    
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
    
    // 重置按钮状态
    const btnRepeat = document.getElementById('btn-repeat');
    const btnNext = document.getElementById('btn-next');
    if (btnRepeat) btnRepeat.disabled = false;
    if (btnNext) btnNext.disabled = true;
}

// 选择答案
function selectAnswer(answer) {
    if (!window.currentQuestion) return;
    
    window.selectedAnswer = answer;
    
    // 禁用所有选项
    document.querySelectorAll('.answer-button, .option-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // 提交答案到后端
    fetch('/api/submit_answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            answer: answer,
            correct_value: window.currentQuestion.correct_value
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

function updateStats(isCorrect) {
    currentTotal++;
    if (isCorrect) {
        currentScore++;
    }
    
    document.getElementById('score').textContent = currentScore;
    document.getElementById('progress').textContent = `${currentTotal}/20`;
    const accuracy = currentTotal > 0 ? Math.round((currentScore / currentTotal) * 100) : 0;
    document.getElementById('accuracy').textContent = `${accuracy}%`;
}

// 显示结果
function showResult(data) {
    const resultDiv = document.getElementById('result-message');
    if (!resultDiv) return;
    
    resultDiv.style.display = 'block';
    resultDiv.className = `result-message ${data.is_correct ? 'correct' : 'incorrect'}`;
    
    // 显示结果
    if (data.is_correct) {
        resultDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                <span style="font-size: 32px;">✅</span>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #166534;">正确！</div>
                </div>
            </div>
        `;
    } else {
        resultDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                <span style="font-size: 32px;">❌</span>
                <div>
                    <div style="font-size: 18px; font-weight: 700; color: #991b1b;">错误！</div>
                    <div style="font-size: 13px; opacity: 0.9; margin-top: 2px;">正确答案：<strong>${data.correct_answer}</strong></div>
                </div>
            </div>
        `;
    }
    
    // 标记正确答案和错误答案
    const selectedAnswer = window.selectedAnswer || '';
    document.querySelectorAll('.answer-button, .option-btn').forEach(btn => {
        btn.disabled = true;
        const btnText = btn.textContent.trim();
        if (data.is_correct && btnText === data.correct_answer) {
            btn.classList.add('--right');
        } else if (!data.is_correct) {
            if (btnText === data.correct_answer) {
                btn.classList.add('--right');
            } else if (btnText === selectedAnswer) {
                btn.classList.add('--wrong');
            }
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
        audioPlayer.play().catch(e => {
            console.error('播放失败:', e);
        });
    }
}

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

// 下一题
function nextQuestion() {
    loadQuestion();
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化默认设置（如果还没有设置）
    if (!sessionStorage.getItem('practice_settings')) {
        const checkedIntervals = Array.from(document.querySelectorAll('input[name="intervals"]:checked')).map(cb => cb.value);
        const checkedDirections = Array.from(document.querySelectorAll('input[name="directions"]:checked')).map(cb => cb.value);
        const defaultSettings = {
            intervals: checkedIntervals.length > 0 ? checkedIntervals : ['minor_second', 'major_second', 'minor_third', 'major_third', 'perfect_fourth', 'perfect_fifth'],
            directions: checkedDirections.length > 0 ? checkedDirections : ['up', 'down'],
            total_questions: '20'
        };
        sessionStorage.setItem('practice_settings', JSON.stringify(defaultSettings));
    }
    
    // 绑定按钮事件
    const btnRepeat = document.getElementById('btn-repeat');
    const btnNext = document.getElementById('btn-next');
    if (btnRepeat) {
        btnRepeat.addEventListener('click', repeatAudio);
    }
    if (btnNext) {
        btnNext.addEventListener('click', nextQuestion);
    }
    
    loadQuestion();
});

