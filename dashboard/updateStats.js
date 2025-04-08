/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "http://ec2-54-69-130-170.us-west-2.compute.amazonaws.com/processing/stats"
const ANALYZER_API_URL = {
    stats: "http://ec2-54-69-130-170.us-west-2.compute.amazonaws.com/analyzer/stats",
    workout: "http://ec2-54-69-130-170.us-west-2.compute.amazonaws.com/analyzer/workout?index=0",
    diet: "http://ec2-54-69-130-170.us-west-2.compute.amazonaws.com/analyzer/diet?index=0"
}
const CONSISTENCY_DATA_URL = "http://ec2-54-69-130-170.us-west-2.compute.amazonaws.com/consistency-check/update"

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    
    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => updateCodeDiv(result, "analyzer-stats"))
    makeReq(ANALYZER_API_URL.workout, (result) => updateCodeDiv(result, "event-workout"))
    makeReq(ANALYZER_API_URL.diet, (result) => updateCodeDiv(result, "event-diet"))
}

const runConsistencyCheck = () => {
    fetch(CONSISTENCY_DATA_URL, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            // Display the consistency check result in the pre tag
            document.getElementById("consistency-result").innerText = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            // Display error if something goes wrong
            document.getElementById("consistency-result").innerText = `Error: ${error.message}`;
        });
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds

    document.getElementById("update-form").addEventListener("submit", (e) => {
        e.preventDefault();  // Prevent page reload
        runConsistencyCheck();  // Trigger the consistency check
    })
}

document.addEventListener('DOMContentLoaded', setup)
