/**
 * app.js — Page initialization and tab logic
 */

// =========================================================================
// TAB SYSTEM
// =========================================================================

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            // Update buttons
            btn.closest('.tab-nav').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Update content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const content = document.getElementById('tab-' + tabId);
            if (content) {
                content.classList.add('active');
                // Resize all charts in the newly visible tab
                setTimeout(() => {
                    content.querySelectorAll('[_echarts_instance_]').forEach(dom => {
                        const inst = echarts.getInstanceByDom(dom);
                        if (inst) inst.resize();
                    });
                }, 50);
            }
        });
    });
}

// =========================================================================
// OVERVIEW PAGE
// =========================================================================

async function initOverview() {
    // Fetch KPI data
    const kpi = await fetchJSON('/api/overview');
    animateKPI('kpi-visits', kpi.total_visits);
    animateKPI('kpi-borrows', kpi.total_borrows);
    animateKPI('kpi-duration', kpi.avg_duration_h);

    // Fetch and render summary charts
    const charts = await fetchJSON('/api/overview/charts');

    const c1 = initChart('chart-monthly-visits');
    if (c1) { registerChart(c1); renderBar(c1, charts.monthly_visits); }

    const c2 = initChart('chart-college-visits');
    if (c2) { registerChart(c2); renderBar(c2, charts.college_visits); }

    const c3 = initChart('chart-borrow-monthly');
    if (c3) { registerChart(c3); renderBar(c3, charts.borrow_monthly); }
}

// =========================================================================
// ACCESS PAGE
// =========================================================================

async function initAccess() {
    // Time analysis (loaded when tab is active)
    loadAccessTime();
}

async function loadAccessTime() {
    const [monthly, daily, weekday, hourly, mDur, mAvgDur, dDur, dAvgDur, wDur, wAvgDur] =
        await Promise.all([
            fetchJSON('/api/access/monthly-visits'),
            fetchJSON('/api/access/daily-visits'),
            fetchJSON('/api/access/weekday-visits'),
            fetchJSON('/api/access/hourly-visits'),
            fetchJSON('/api/access/monthly-duration'),
            fetchJSON('/api/access/monthly-avg-duration'),
            fetchJSON('/api/access/daily-duration'),
            fetchJSON('/api/access/daily-avg-duration'),
            fetchJSON('/api/access/weekday-duration'),
            fetchJSON('/api/access/weekday-avg-duration'),
        ]);

    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-monthly-visits', monthly, renderBar);
    makeChart('chart-daily-visits', daily, (c, d) => renderLine(c, d, { area: true }));
    makeChart('chart-weekday-visits', weekday, renderBar);
    makeChart('chart-hourly-visits', hourly, (c, d) => renderLine(c, d, { smooth: true }));
    makeChart('chart-monthly-duration', mDur, renderBar);
    makeChart('chart-monthly-avg-duration', mAvgDur, renderBar);
    makeChart('chart-daily-duration', dDur, (c, d) => renderLine(c, d, { area: true }));
    makeChart('chart-daily-avg-duration', dAvgDur, renderBar);
    makeChart('chart-weekday-duration', wDur, renderBar);
    makeChart('chart-weekday-avg-duration', wAvgDur, renderBar);

    // Load college analysis in parallel
    loadAccessCollege();
    // Load major analysis
    loadAccessMajor();
    // Load student analysis
    loadAccessStudent();
}

async function loadAccessCollege() {
    const [visits, students, dur, avgDur, mVisits, mDur] = await Promise.all([
        fetchJSON('/api/access/college-visits'),
        fetchJSON('/api/access/college-students'),
        fetchJSON('/api/access/college-duration'),
        fetchJSON('/api/access/college-avg-duration'),
        fetchJSON('/api/access/college-monthly-visits'),
        fetchJSON('/api/access/college-monthly-duration'),
    ]);

    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-college-visits', visits, renderBar);
    makeChart('chart-college-students', students, renderBar);
    makeChart('chart-college-duration', dur, renderHorizontalBar);
    makeChart('chart-college-avg-duration', avgDur, renderHorizontalBar);
    makeChart('chart-college-monthly-visits', mVisits, renderMultiLine);
    makeChart('chart-college-monthly-duration', mDur, renderMultiLine);
}

async function loadAccessMajor() {
    const [majorV, majorD, classV, classD] = await Promise.all([
        fetchJSON('/api/access/major-visits'),
        fetchJSON('/api/access/major-duration'),
        fetchJSON('/api/access/class-visits'),
        fetchJSON('/api/access/class-duration'),
    ]);

    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-major-visits', majorV, renderHorizontalBar);
    makeChart('chart-major-duration', majorD, renderHorizontalBar);
    makeChart('chart-class-visits', classV, renderHorizontalBar);
    makeChart('chart-class-duration', classD, renderHorizontalBar);
}

async function loadAccessStudent() {
    const [topV, topD, visitBox, durBox, scatter] = await Promise.all([
        fetchJSON('/api/access/student-top-visits'),
        fetchJSON('/api/access/student-top-duration'),
        fetchJSON('/api/access/college-visit-boxplot'),
        fetchJSON('/api/access/college-duration-boxplot'),
        fetchJSON('/api/access/scatter'),
    ]);

    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-student-top-visits', topV, renderHorizontalBar);
    makeChart('chart-student-top-duration', topD, renderHorizontalBar);
    makeChart('chart-visit-boxplot', visitBox, renderBoxplot);
    makeChart('chart-duration-boxplot', durBox, renderBoxplot);
    makeChart('chart-scatter', scatter, renderScatter);
}

// =========================================================================
// BORROWING PAGE
// =========================================================================

async function initBorrowing() {
    const [monthly, hourly, college, perCapita, major, cls, topBooks, dur, colDur] =
        await Promise.all([
            fetchJSON('/api/borrowing/monthly'),
            fetchJSON('/api/borrowing/hourly'),
            fetchJSON('/api/borrowing/college'),
            fetchJSON('/api/borrowing/college-per-capita'),
            fetchJSON('/api/borrowing/major'),
            fetchJSON('/api/borrowing/classifications'),
            fetchJSON('/api/borrowing/top-books'),
            fetchJSON('/api/borrowing/duration'),
            fetchJSON('/api/borrowing/college-duration'),
        ]);

    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-borrow-monthly', monthly, renderBar);
    makeChart('chart-borrow-hourly', hourly, (c, d) => renderLine(c, d, { smooth: true }));
    makeChart('chart-borrow-college', college, renderBar);
    makeChart('chart-borrow-college-per-capita', perCapita, renderHorizontalBar);
    makeChart('chart-borrow-major', major, renderHorizontalBar);
    makeChart('chart-borrow-classifications', cls, renderBar);
    makeChart('chart-borrow-top-books', topBooks, renderHorizontalBar);
    makeChart('chart-borrow-duration', dur, renderBar);
    makeChart('chart-borrow-college-duration', colDur, renderHorizontalBar);
}
