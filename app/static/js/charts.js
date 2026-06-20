/**
 * charts.js — ECharts rendering helpers for NSU Library Dashboard
 */

// Color palette (matches existing PyEcharts darkblue theme)
const COLORS = {
    primary: '#1a3a5c',
    accent: '#4a90d9',
    gradient: ['#1a3a5c', '#2a5a8c', '#4a90d9', '#6ab0f9'],
    series: ['#1a3a5c', '#c23531', '#2f4554', '#61a0a8', '#d48265', '#91c7ae'],
    background: 'transparent',
};

/**
 * Show a loading spinner on a chart container.
 */
function showLoading(chart) {
    chart.showLoading({
        text: '加载中...',
        color: COLORS.accent,
        textColor: '#999',
        maskColor: 'rgba(255,255,255,0.8)',
    });
}

/**
 * Initialize a chart on an element by ID, with loading state.
 */
function initChart(containerId) {
    const dom = document.getElementById(containerId);
    if (!dom) return null;
    const chart = echarts.init(dom);
    showLoading(chart);
    return chart;
}

/**
 * Fetch JSON from an API endpoint.
 */
async function fetchJSON(url) {
    const resp = await fetch(url);
    return resp.json();
}

// =========================================================================
// RENDER FUNCTIONS
// =========================================================================

/**
 * Render a vertical bar chart.
 */
function renderBar(chart, data, opts = {}) {
    const isHorizontal = opts.horizontal || false;
    const axis = isHorizontal ? {
        xAxis: { type: 'value', name: data.x_label || '' },
        yAxis: { type: 'category', data: data.y, axisLabel: { width: 120, overflow: 'truncate' } },
        seriesData: [{ data: data.x, type: 'bar', itemStyle: { color: COLORS.primary },
            label: { show: true, position: 'right', fontSize: 11 } }],
    } : {
        xAxis: { type: 'category', data: data.x, axisLabel: { rotate: data.x.length > 8 ? 30 : 0 } },
        yAxis: { type: 'value', name: data.y_label || '' },
        seriesData: [{ data: data.y, type: 'bar', itemStyle: { color: COLORS.primary },
            label: { show: true, position: 'top', fontSize: 11 } }],
    };

    const markLine = data.avg !== undefined ? {
        markLine: {
            silent: true,
            data: [{ yAxis: data.avg, name: '平均值' }],
            label: { formatter: `{c}` },
            lineStyle: { color: '#c23531', type: 'dashed' },
        }
    } : {};

    chart.hideLoading();
    chart.setOption({
        title: { text: data.title || '', left: 'center', top: 0 },
        tooltip: { trigger: 'axis' },
        grid: { left: isHorizontal ? 150 : 60, right: 40, bottom: 40, top: 50 },
        ...axis,
        series: [{ ...axis.seriesData[0], ...markLine }],
    });
    chart.resize();
}

/**
 * Render a horizontal bar chart (reversed axis).
 */
function renderHorizontalBar(chart, data) {
    renderBar(chart, data, { horizontal: true });
}

/**
 * Render a line/area chart.
 */
function renderLine(chart, data, opts = {}) {
    const isArea = opts.area || false;
    const isSmooth = opts.smooth || false;

    const markLine = data.avg !== undefined ? {
        markLine: {
            silent: true,
            data: [{ yAxis: data.avg, name: '平均值' }],
            label: { formatter: `{c}` },
            lineStyle: { color: '#c23531', type: 'dashed' },
        }
    } : {};

    chart.hideLoading();
    chart.setOption({
        title: { text: data.title || '', left: 'center', top: 0 },
        tooltip: { trigger: 'axis' },
        grid: { left: 60, right: 40, bottom: 40, top: 50 },
        xAxis: { type: 'category', data: data.x, name: data.x_label || '' },
        yAxis: { type: 'value', name: data.y_label || '' },
        series: [{
            type: 'line',
            data: data.y,
            smooth: isSmooth,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 3, color: COLORS.primary },
            itemStyle: { color: COLORS.primary },
            areaStyle: isArea ? { opacity: 0.3, color: COLORS.accent } : undefined,
            ...markLine,
        }],
    });
    chart.resize();
}

/**
 * Render a multi-series line chart (e.g., per-college trends).
 */
function renderMultiLine(chart, data) {
    const seriesNames = Object.keys(data.series);
    const series = seriesNames.map((name, i) => ({
        name: name,
        type: 'line',
        data: data.series[name],
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 3 },
    }));

    chart.hideLoading();
    chart.setOption({
        title: { text: data.title || '', left: 'center', top: 0 },
        tooltip: { trigger: 'axis' },
        legend: { right: 20, top: 30, orient: 'vertical' },
        grid: { left: 60, right: 160, bottom: 40, top: 60 },
        xAxis: { type: 'category', data: data.x, name: data.x_label || '' },
        yAxis: { type: 'value', name: data.y_label || '' },
        series: series,
        color: COLORS.series,
    });
    chart.resize();
}

/**
 * Render a scatter plot (optionally with regression line).
 */
function renderScatter(chart, data) {
    const scatterData = data.x.map((x, i) => [x, data.y[i]]);
    const series = [{
        type: 'scatter',
        data: scatterData,
        symbolSize: 4,
        itemStyle: { color: COLORS.accent, opacity: 0.5 },
    }];

    if (data.regression) {
        series.push({
            type: 'line',
            data: [data.regression.x.map((x, i) => [x, data.regression.y[i]])][0],
            symbol: 'none',
            lineStyle: { color: '#c23531', width: 2, type: 'dashed' },
            name: `y = ${data.regression.slope}x + ${data.regression.intercept}`,
        });
    }

    chart.hideLoading();
    chart.setOption({
        title: { text: data.title || '', left: 'center', top: 0 },
        tooltip: {
            trigger: 'item',
            formatter: params => {
                if (params.seriesType === 'scatter') {
                    return `${data.x_label}: ${params.value[0]}<br>${data.y_label}: ${params.value[1]}`;
                }
                return params.seriesName || '';
            }
        },
        legend: data.regression ? { bottom: 10 } : undefined,
        grid: { left: 60, right: 40, bottom: 50, top: 50 },
        xAxis: { type: 'value', name: data.x_label || '' },
        yAxis: { type: 'value', name: data.y_label || '' },
        series: series,
    });
    chart.resize();
}

/**
 * Render a boxplot chart.
 * Data format: { categories: [...], data: [[val1, val2, ...], ...] }
 */
function renderBoxplot(chart, data) {
    // Compute boxplot statistics for each category
    const boxData = data.data.map(vals => computeBoxplotStats(vals));

    chart.hideLoading();
    chart.setOption({
        title: { text: data.title || '', left: 'center', top: 0 },
        tooltip: {
            trigger: 'item',
            formatter: params => {
                if (params.componentType === 'series') {
                    const d = params.data;
                    return `${params.name}<br>` +
                        `最大值: ${d[4]}<br>上四分位: ${d[3]}<br>` +
                        `中位数: ${d[2]}<br>下四分位: ${d[1]}<br>最小值: ${d[0]}`;
                }
            }
        },
        grid: { left: 80, right: 40, bottom: 40, top: 50 },
        xAxis: { type: 'category', data: data.categories, axisLabel: { rotate: 15 } },
        yAxis: { type: 'value', name: data.y_label || '' },
        series: [{
            type: 'boxplot',
            data: boxData,
            itemStyle: { color: COLORS.accent, borderColor: COLORS.primary },
        }],
    });
    chart.resize();
}

/**
 * Compute [min, Q1, median, Q3, max] for boxplot.
 */
function computeBoxplotStats(sortedVals) {
    if (!sortedVals || sortedVals.length === 0) return [0, 0, 0, 0, 0];
    const arr = sortedVals.slice().sort((a, b) => a - b);
    const n = arr.length;
    const q1 = arr[Math.floor(n * 0.25)];
    const median = arr[Math.floor(n * 0.5)];
    const q3 = arr[Math.floor(n * 0.75)];
    // Use 1.5*IQR for whiskers
    const iqr = q3 - q1;
    const lo = Math.max(arr[0], q1 - 1.5 * iqr);
    const hi = Math.min(arr[n - 1], q3 + 1.5 * iqr);
    return [Math.round(lo * 100) / 100, Math.round(q1 * 100) / 100,
            Math.round(median * 100) / 100, Math.round(q3 * 100) / 100,
            Math.round(hi * 100) / 100];
}

/**
 * Animate a KPI counter from 0 to target value.
 */
function animateKPI(elementId, target, suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;
    const duration = 1500;
    const start = performance.now();
    const isFloat = String(target).includes('.');

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = isFloat
            ? (target * eased).toFixed(2)
            : Math.floor(target * eased).toLocaleString();
        el.textContent = current + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// =========================================================================
// RESIZE HANDLER
// =========================================================================

const chartInstances = [];

function registerChart(chart) {
    if (chart) chartInstances.push(chart);
}

window.addEventListener('resize', () => {
    chartInstances.forEach(c => c && c.resize());
});
