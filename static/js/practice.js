// 练习页面JavaScript

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
    const exerciseType = window.exerciseType;
    
    let questionHtml = '';
    
    if (exerciseType === 'interval') {
        questionHtml = `
            <div class="audio-player-container">
                <h3>🎧 请听音程，选择正确的音程名称：</h3>
                <audio id="audioPlayer" controls preload="auto">
                    <source src="/static/audio/${data.audio_file}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
                <br>
                <button class="btn" onclick="playAudio()">
                    <span>▶️</span> 播放音频
                </button>
            </div>
            <div class="options-grid" id="options-grid">
                ${data.options.map((option, index) => `
                    <button class="option-btn" onclick="selectAnswer('${data.option_values[index]}')">
                        ${option}
                    </button>
                `).join('')}
            </div>
        `;
    } else if (exerciseType === 'scale_degree') {
        questionHtml = `
            <div class="audio-player-container">
                <h3>🎧 请听音符，选择它在音阶中的音级：</h3>
                <p style="font-size: 13px; color: var(--hf-text-secondary); margin-bottom: 12px;">
                    当前音阶：<strong>${data.scale_name || ''}</strong>
                </p>
                <audio id="audioPlayer" controls preload="auto">
                    <source src="/static/audio/${data.audio_file}" type="audio/wav">
                    您的浏览器不支持音频播放。
                </audio>
                <br>
                <button class="btn" onclick="playAudio()">
                    <span>▶️</span> 播放题目音频
                </button>
            </div>
            <div class="reference-audio-container" style="margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--hf-border);">
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--hf-text-primary);">参考音频：</h4>
                <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 12px; color: var(--hf-text-secondary); margin-bottom: 6px; display: block;">根音：</label>
                        <audio controls preload="auto" style="width: 100%;">
                            <source src="/static/audio/${data.root_audio_file}" type="audio/wav">
                        </audio>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <label style="font-size: 12px; color: var(--hf-text-secondary); margin-bottom: 6px; display: block;">完整音阶：</label>
                        <audio controls preload="auto" style="width: 100%;">
                            <source src="/static/audio/${data.scale_audio_file}" type="audio/wav">
                        </audio>
                    </div>
                </div>
            </div>
            <div class="options-grid" id="options-grid" style="margin-top: 24px;">
                ${data.options.map((option) => `
                    <button class="option-btn" onclick="selectAnswer('${option}')">
                        ${option}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    questionArea.innerHTML = questionHtml + '<div id="result-message" style="display: none;"></div>';
}

// 选择答案
function selectAnswer(answer) {
    if (!window.currentQuestion) return;
    
    // 禁用所有选项
    document.querySelectorAll('.option-btn').forEach(btn => {
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
    resultDiv.style.display = 'block';
    resultDiv.className = `result-message ${data.is_correct ? 'correct' : 'incorrect'}`;
    resultDiv.innerHTML = data.is_correct 
        ? `✅ 正确！`
        : `❌ 错误！正确答案：${data.correct_answer}`;
    
    // 禁用所有选项
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // 2秒后加载下一题
    setTimeout(() => {
        loadQuestion();
    }, 2000);
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
    loadQuestion();
});

