const BACKEND_URL = "http://127.0.0.1:5000";

let historyChart = null;
let forecastChart = null;

let selectedHistoryDays = 1;


/* =========================
   PAGE LOAD
========================= */

document.addEventListener("DOMContentLoaded", () => {

    loadEnvironment();

    setTimeout(() => {
        loadHistory(selectedHistoryDays);
        checkDatabase();
    }, 300);

    setTimeout(() => {
        loadForecast();
    }, 800);

});


/* =========================
   ENVIRONMENT DATA
========================= */

async function loadEnvironment() {

    try {

        const response =
            await fetch(`${BACKEND_URL}/environment`);

        if (!response.ok) {
            throw new Error("Environment API error");
        }

        const data =
            await response.json();

        console.log("Environment data:", data);

        const aqi =
            Number(data.aqi);

        setText(
            "aqiValue",
            Number.isFinite(aqi)
                ? Math.round(aqi)
                : "--"
        );

        const category =
            getAQICategory(aqi);

        setText(
            "riskValue",
            category.name
        );

        setText(
            "aqiDescription",
            category.description
        );

        updateAQICard(category);

        updateAlertSystem(
            aqi,
            category
        );


        /* POLLUTANTS */

        setText(
            "pm25Result",
            formatNumber(
                data.air_quality?.pm2_5
            )
        );

        setText(
            "pm10Result",
            formatNumber(
                data.air_quality?.pm10
            )
        );

        setText(
            "no2Value",
            formatNumber(
                data.air_quality?.nitrogen_dioxide
            )
        );

        setText(
            "so2Value",
            formatNumber(
                data.air_quality?.sulphur_dioxide
            )
        );

        setText(
            "coValue",
            formatNumber(
                data.air_quality?.carbon_monoxide
            )
        );

        setText(
            "o3Value",
            formatNumber(
                data.air_quality?.ozone
            )
        );


        /* WEATHER */

        setText(
            "temperatureValue",
            formatNumber(
                data.weather?.temperature_2m
            )
        );

        setText(
            "humidityValue",
            formatNumber(
                data.weather?.relative_humidity_2m
            )
        );

        setText(
            "windValue",
            formatNumber(
                data.weather?.wind_speed_10m
            )
        );

        setText(
            "windDirectionValue",
            formatNumber(
                data.weather?.wind_direction_10m
            )
        );

        setText(
            "rainfallValue",
            formatNumber(
                data.weather?.rain
            )
        );


        /* PROGRESS BARS */

        const pm25 =
            Number(
                data.air_quality?.pm2_5 || 0
            );

        const wind =
            Number(
                data.weather?.wind_speed_10m || 0
            );


        setWidth(
            "pm25Bar",
            Math.min(
                Math.max(pm25, 0),
                100
            )
        );


        setWidth(
            "windBar",
            Math.min(
                Math.max(wind * 5, 0),
                100
            )
        );


        /* AI ANALYSIS */

        setText(
            "aiExplanation",
            category.analysis
        );


        /* LAST UPDATED */

        setText(
            "lastUpdated",
            getCurrentTime()
        );


    } catch (error) {

        console.error(
            "Environment loading error:",
            error
        );


        setText(
            "aqiValue",
            "--"
        );

        setText(
            "riskValue",
            "Data unavailable"
        );

        setText(
            "aqiDescription",
            "Unable to fetch the latest environmental data."
        );

        setText(
            "alertTitle",
            "Data Connection Alert"
        );

        setText(
            "alertLevel",
            "OFFLINE"
        );

        setText(
            "alertMessage",
            "Current environmental data could not be retrieved."
        );

        setText(
            "alertAction",
            "Please check that the Flask backend is running."
        );

        setText(
            "lastUpdated",
            "Unavailable"
        );

    }

}


/* =========================
   AQI CATEGORY
========================= */

function getAQICategory(aqi) {

    if (!Number.isFinite(aqi)) {

        return {

            name: "Unavailable",

            className: "",

            icon: "❔",

            description:
                "AQI data is currently unavailable.",

            alertTitle:
                "Air Quality Status",

            message:
                "Waiting for current air quality data.",

            action:
                "Please check the data connection.",

            analysis:
                "Environmental analysis will be available after current AQI data is received."

        };

    }


    if (aqi <= 50) {

        return {

            name: "Good",

            className: "good",

            icon: "🟢",

            description:
                "Air quality is currently good.",

            alertTitle:
                "Air Quality is Good",

            message:
                "Pollution levels are currently low.",

            action:
                "Normal outdoor activities can continue.",

            analysis:
                "Air quality is good and pollution levels are currently low. Environmental conditions are generally favorable."

        };

    }


    if (aqi <= 100) {

        return {

            name: "Moderate",

            className: "moderate",

            icon: "🟡",

            description:
                "Air quality is currently moderate.",

            alertTitle:
                "Moderate Air Quality",

            message:
                "Air quality is acceptable, but some people may be more sensitive.",

            action:
                "Sensitive individuals can monitor air quality before prolonged outdoor activity.",

            analysis:
                "Air quality is moderate. Pollution levels are elevated compared with the good range, so sensitive individuals should monitor conditions."

        };

    }


    if (aqi <= 200) {

        return {

            name: "Poor",

            className: "poor",

            icon: "🟠",

            description:
                "Air quality is currently poor.",

            alertTitle:
                "Poor Air Quality",

            message:
                "Pollution levels are elevated.",

            action:
                "Consider reducing prolonged outdoor exposure.",

            analysis:
                "Air quality is poor. Higher pollution levels may cause discomfort for some people, especially during prolonged outdoor exposure."

        };

    }


    if (aqi <= 300) {

        return {

            name: "Very Poor",

            className: "very-poor",

            icon: "🔴",

            description:
                "Air quality is currently very poor.",

            alertTitle:
                "Very Poor Air Quality",

            message:
                "High pollution levels are currently detected.",

            action:
                "Reduce prolonged outdoor exposure and monitor air quality updates.",

            analysis:
                "Air pollution is very high. Reducing prolonged outdoor exposure can help limit exposure to elevated pollution levels."

        };

    }


    return {

        name: "Severe",

        className: "severe",

        icon: "🚨",

        description:
            "Air quality is currently severe.",

        alertTitle:
            "Severe Air Quality",

        message:
            "Very high pollution levels are currently detected.",

        action:
            "Avoid unnecessary prolonged outdoor exposure and monitor official air-quality guidance.",

        analysis:
            "Air pollution is at a severe level. Environmental conditions should be monitored closely and prolonged outdoor exposure should be minimized."

    };

}


/* =========================
   AQI CARD
========================= */

function updateAQICard(category) {

    const aqiCard =
        document.getElementById(
            "aqiCard"
        );

    const risk =
        document.getElementById(
            "riskValue"
        );


    if (!aqiCard || !risk) {
        return;
    }


    aqiCard.classList.remove(
        "aqi-good",
        "aqi-moderate",
        "aqi-poor",
        "aqi-very-poor",
        "aqi-severe"
    );


    risk.classList.remove(
        "risk-good",
        "risk-moderate",
        "risk-poor",
        "risk-very-poor",
        "risk-severe"
    );


    if (category.className) {

        aqiCard.classList.add(
            `aqi-${category.className}`
        );

        risk.classList.add(
            `risk-${category.className}`
        );

    }

}


/* =========================
   ALERT SYSTEM
========================= */

function updateAlertSystem(
    aqi,
    category
) {

    const alertCard =
        document.getElementById(
            "alertCard"
        );


    if (!alertCard) {
        return;
    }


    alertCard.classList.remove(
        "alert-good",
        "alert-moderate",
        "alert-poor",
        "alert-very-poor",
        "alert-severe"
    );


    if (category.className) {

        alertCard.classList.add(
            `alert-${category.className}`
        );

    }


    setText(
        "alertIcon",
        category.icon
    );

    setText(
        "alertTitle",
        category.alertTitle
    );

    setText(
        "alertLevel",
        category.name.toUpperCase()
    );

    setText(
        "alertMessage",
        category.message
    );

    setText(
        "alertAction",
        category.action
    );

}


/* =========================
   HISTORICAL DATA
========================= */

async function loadHistory(days = 1) {

    selectedHistoryDays =
        days;


    updateHistoryButtons(days);


    try {

        setText(
            "historyMessage",
            `Loading ${getHistoryLabel(days)} historical data...`
        );


        const response =
            await fetch(
                `${BACKEND_URL}/history?days=${days}`
            );


        if (!response.ok) {

            throw new Error(
                "History API error"
            );

        }


        const result =
            await response.json();


        console.log(
            "History:",
            result
        );


        if (
            !result.data ||
            result.data.length === 0
        ) {

            setText(
                "historyMessage",
                `No historical data available for ${getHistoryLabel(days)}.`
            );


            if (historyChart) {

                historyChart.destroy();

                historyChart = null;

            }

            return;

        }


        setText(
            "historyMessage",
            `${result.count} readings available • ${getHistoryLabel(days)}`
        );


        const historyData =
            [...result.data].reverse();


        const labels =
            historyData.map(
                item =>
                    formatChartTime(
                        item.timestamp
                    )
            );


        const values =
            historyData.map(
                item =>
                    item.aqi
            );


        const canvas =
            document.getElementById(
                "historyChart"
            );


        if (!canvas) {
            return;
        }


        if (historyChart) {
            historyChart.destroy();
        }


        historyChart =
            new Chart(
                canvas,
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label: "AQI",

                                data: values,

                                borderWidth: 3,

                                pointRadius: 2,

                                pointHoverRadius: 5,

                                tension: 0.35,

                                fill: true,

                                backgroundColor:
                                    "rgba(37, 99, 235, 0.08)",

                                borderColor:
                                    "#2563eb"

                            }

                        ]

                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        interaction: {

                            intersect: false,

                            mode: "index"

                        },


                        plugins: {

                            legend: {

                                display: true

                            },


                            tooltip: {

                                callbacks: {

                                    label:
                                        function(context) {

                                            return ` AQI: ${context.raw}`;

                                        }

                                }

                            }

                        },


                        scales: {

                            x: {

                                ticks: {

                                    maxTicksLimit: 10

                                }

                            },


                            y: {

                                beginAtZero: true

                            }

                        }

                    }

                }
            );

    }


    catch (error) {

        console.error(
            "History loading error:",
            error
        );


        setText(
            "historyMessage",
            "History could not be loaded."
        );

    }

}


/* =========================
   HISTORY BUTTONS
========================= */

function updateHistoryButtons(days) {

    const today =
        document.getElementById(
            "todayBtn"
        );

    const sevenDays =
        document.getElementById(
            "sevenDaysBtn"
        );

    const thirtyDays =
        document.getElementById(
            "thirtyDaysBtn"
        );


    if (today) {
        today.classList.remove(
            "active-filter"
        );
    }


    if (sevenDays) {
        sevenDays.classList.remove(
            "active-filter"
        );
    }


    if (thirtyDays) {
        thirtyDays.classList.remove(
            "active-filter"
        );
    }


    if (days === 1 && today) {

        today.classList.add(
            "active-filter"
        );

    }


    if (days === 7 && sevenDays) {

        sevenDays.classList.add(
            "active-filter"
        );

    }


    if (days === 30 && thirtyDays) {

        thirtyDays.classList.add(
            "active-filter"
        );

    }

}


/* =========================
   HISTORY LABEL
========================= */

function getHistoryLabel(days) {

    if (days === 1) {
        return "Today";
    }

    if (days === 7) {
        return "Last 7 Days";
    }

    if (days === 30) {
        return "Last 30 Days";
    }

    return `${days} Days`;

}


/* =========================
   ML FORECAST
========================= */

async function loadForecast() {

    try {

        setText(
            "forecastMessage",
            "Loading ML forecast..."
        );


        const response =
            await fetch(
                `${BACKEND_URL}/forecast`
            );


        if (!response.ok) {

            throw new Error(
                "Forecast API error"
            );

        }


        const result =
            await response.json();


        console.log(
            "ML Forecast:",
            result
        );


        if (result.summary) {

            const forecast24 =
                result.summary["24_hour"];

            const forecast48 =
                result.summary["48_hour"];

            const forecast72 =
                result.summary["72_hour"];


            setText(
                "forecast24",
                formatAQI(
                    forecast24
                )
            );


            setText(
                "forecast48",
                formatAQI(
                    forecast48
                )
            );


            setText(
                "forecast72",
                formatAQI(
                    forecast72
                )
            );


            setForecastCategory(
                "forecast24Category",
                forecast24
            );


            setForecastCategory(
                "forecast48Category",
                forecast48
            );


            setForecastCategory(
                "forecast72Category",
                forecast72
            );

        }


        if (
            !result.forecast ||
            result.forecast.length === 0
        ) {

            setText(
                "forecastMessage",
                "ML forecast loaded, but no forecast points are available."
            );

            return;

        }


        const labels =
            result.forecast.map(
                item =>
                    `+${item.hour}h`
            );


        const values =
            result.forecast.map(
                item =>
                    item.aqi
            );


        const canvas =
            document.getElementById(
                "aqiForecastChart"
            );


        if (!canvas) {
            return;
        }


        if (forecastChart) {
            forecastChart.destroy();
        }


        forecastChart =
            new Chart(
                canvas,
                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                label:
                                    "Predicted AQI",

                                data: values,

                                borderWidth: 3,

                                pointRadius: 2,

                                pointHoverRadius: 5,

                                tension: 0.35,

                                fill: true,

                                backgroundColor:
                                    "rgba(124, 58, 237, 0.08)",

                                borderColor:
                                    "#7c3aed"

                            }

                        ]

                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        interaction: {

                            intersect: false,

                            mode: "index"

                        },


                        plugins: {

                            legend: {

                                display: true

                            },


                            tooltip: {

                                callbacks: {

                                    label:
                                        function(context) {

                                            return ` Predicted AQI: ${context.raw}`;

                                        }

                                }

                            }

                        },


                        scales: {

                            x: {

                                ticks: {

                                    maxTicksLimit: 12

                                }

                            },


                            y: {

                                beginAtZero: true

                            }

                        }

                    }

                }
            );


        setText(
            "forecastMessage",
            "ML forecast loaded successfully • 72-hour prediction available"
        );


    } catch (error) {

        console.error(
            "ML Forecast error:",
            error
        );


        setText(
            "forecastMessage",
            "ML forecast is temporarily unavailable."
        );

    }

}


/* =========================
   FORECAST CATEGORY
========================= */

function setForecastCategory(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (!element) {
        return;
    }


    const aqi =
        Number(value);


    if (!Number.isFinite(aqi)) {

        element.textContent =
            "Unavailable";

        return;

    }


    const category =
        getAQICategory(aqi);


    element.textContent =
        category.name;

}


/* =========================
   DATABASE STATUS
========================= */

async function checkDatabase() {

    try {

        const response =
            await fetch(
                `${BACKEND_URL}/database-status`
            );


        if (!response.ok) {

            throw new Error(
                "Database API error"
            );

        }


        const data =
            await response.json();


        console.log(
            "Database:",
            data
        );


        if (
            data.status ===
            "connected"
        ) {

            setText(
                "databaseStatus",
                `● Database connected • ${data.total_readings} readings`
            );

        } else {

            setText(
                "databaseStatus",
                "● Database unavailable"
            );

        }


    } catch (error) {

        console.error(
            "Database error:",
            error
        );


        setText(
            "databaseStatus",
            "● Database unavailable"
        );

    }

}


/* =========================
   AUTO REFRESH
========================= */

setInterval(() => {

    console.log(
        "Refreshing environmental dashboard..."
    );


    loadEnvironment();

    loadHistory(
        selectedHistoryDays
    );

    checkDatabase();

    loadForecast();

}, 5 * 60 * 1000);


/* =========================
   HELPER FUNCTIONS
========================= */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value;

    }

}


function setWidth(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.style.width =
            `${value}%`;

    }

}


function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "--";

    }


    const number =
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        return "--";

    }


    return Number(
        number.toFixed(2)
    );

}


function formatAQI(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "--";

    }


    const number =
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        return "--";

    }


    return Math.round(number);

}


function getCurrentTime() {

    const now =
        new Date();


    return now.toLocaleTimeString(
        [],
        {

            hour: "2-digit",

            minute: "2-digit",

            second: "2-digit"

        }
    );

}


function formatChartTime(
    timestamp
) {

    if (!timestamp) {
        return "";
    }


    const date =
        new Date(timestamp);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return timestamp;

    }


    return date.toLocaleString(
        [],
        {

            month: "short",

            day: "numeric",

            hour: "2-digit",

            minute: "2-digit"

        }
    );

}