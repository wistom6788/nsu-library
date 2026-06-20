/**
 * student.js — Student search and detail page
 */

async function searchStudent() {
    const query = document.getElementById('student-search').value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="search-loading">搜索中...</div>';

    try {
        const data = await fetchJSON(`/api/student/search?q=${encodeURIComponent(query)}`);
        if (data.results.length === 0) {
            resultsDiv.innerHTML = '<div class="search-empty">未找到匹配的学生</div>';
            return;
        }

        let html = '<div class="search-list">';
        data.results.forEach(stu => {
            html += `<div class="search-item" onclick="loadStudentDetail('${stu.student_id}')">
                <span class="search-name">${stu.name}</span>
                <span class="search-id">${stu.student_id}</span>
                <span class="search-college">${stu.college}</span>
                <span class="search-major">${stu.major}</span>
            </div>`;
        });
        html += '</div>';
        resultsDiv.innerHTML = html;
    } catch (e) {
        resultsDiv.innerHTML = '<div class="search-error">搜索出错，请重试</div>';
    }
}

async function loadStudentDetail(studentId) {
    const detailDiv = document.getElementById('student-detail');
    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '';

    try {
        const data = await fetchJSON(`/api/student/${studentId}`);
        if (data.error) {
            resultsDiv.innerHTML = `<div class="search-error">${data.error}</div>`;
            return;
        }

        // Show detail section
        detailDiv.style.display = 'block';

        // Fill student info
        document.getElementById('stu-name').textContent = data.info.name;
        document.getElementById('stu-id').textContent = data.info.student_id;
        document.getElementById('stu-college').textContent = data.info.college;
        document.getElementById('stu-major').textContent = data.info.major;
        document.getElementById('stu-class').textContent = data.info.class_name;

        // KPI cards
        const kpiDiv = document.getElementById('student-kpis');
        const access = data.access || {};
        const borrow = data.borrow || {};
        kpiDiv.innerHTML = `
            <div class="kpi-card">
                <div class="kpi-icon">🚪</div>
                <div class="kpi-content">
                    <div class="kpi-value">${access.total_visits || 0}</div>
                    <div class="kpi-label">到馆次数</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-content">
                    <div class="kpi-value">${access.total_duration_h || 0}h</div>
                    <div class="kpi-label">在馆总时长</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">📖</div>
                <div class="kpi-content">
                    <div class="kpi-value">${borrow.total_borrows || 0}</div>
                    <div class="kpi-label">借阅次数</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon">📅</div>
                <div class="kpi-content">
                    <div class="kpi-value">${access.first_visit || '—'}</div>
                    <div class="kpi-label">首次到馆</div>
                </div>
            </div>
        `;

        // Charts
        renderStudentCharts(data);
    } catch (e) {
        resultsDiv.innerHTML = '<div class="search-error">加载学生数据出错</div>';
    }
}

function renderStudentCharts(data) {
    // Destroy old charts
    ['chart-stu-monthly-visits', 'chart-stu-hourly-visits',
     'chart-stu-weekday-visits', 'chart-stu-monthly-borrows'].forEach(id => {
        const dom = document.getElementById(id);
        if (dom) {
            const old = echarts.getInstanceByDom(dom);
            if (old) old.dispose();
        }
    });

    const access = data.access || {};
    const borrow = data.borrow || {};

    // Monthly visits
    if (access.monthly_visits) {
        const c = initChart('chart-stu-monthly-visits');
        if (c) {
            registerChart(c);
            renderBar(c, {
                ...access.monthly_visits,
                title: '每月到馆次数',
                x_label: '月份',
                y_label: '次数',
            });
        }
    }

    // Hourly visits
    if (access.hourly_visits) {
        const c = initChart('chart-stu-hourly-visits');
        if (c) {
            registerChart(c);
            renderLine(c, {
                ...access.hourly_visits,
                title: '到馆时间分布',
                x_label: '小时',
                y_label: '次数',
            }, { smooth: true });
        }
    }

    // Weekday visits
    if (access.weekday_visits) {
        const c = initChart('chart-stu-weekday-visits');
        if (c) {
            registerChart(c);
            renderBar(c, {
                ...access.weekday_visits,
                title: '每周各天到馆次数',
                x_label: '星期',
                y_label: '次数',
            });
        }
    }

    // Monthly borrows
    if (borrow.monthly_borrows) {
        const c = initChart('chart-stu-monthly-borrows');
        if (c) {
            registerChart(c);
            renderBar(c, {
                ...borrow.monthly_borrows,
                title: '每月借书次数',
                x_label: '月份',
                y_label: '次数',
            });
        }
    }
}
