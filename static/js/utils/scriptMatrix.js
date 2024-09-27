
function updateRangInput(inputField) {
    var rIn = document.getElementById('rIn');
    var rInValue = document.getElementById('rInValue');
    var rOut = document.getElementById('rOut');
    var rOutValue = document.getElementById('rOutValue');
    if (inputField == 'rIn') {
        if (rIn.value <= 0) {
            rIn.value = 10;
            rInValue.value = 10;
        }
        if (rIn.value >= 90) {
            rIn.value = 90;
            rInValue.value = 90;
        }
        rInValue.value = rIn.value
        var calculatedRout = parseInt(rIn.value) + 10;
        rOut.value = calculatedRout > 100 ? 100 : calculatedRout;
        rOutValue.value = rOut.value;
    }
    if (inputField == 'rInValue') {
        if (rInValue.value <= 0) {
            rIn.value = 1;
            rInValue.value = 1;
        }
        if (rInValue.value >= 99) {
            rIn.value = 99;
            rInValue.value = 99;
        }
        rIn.value = rInValue.value;
        var calculatedRout
        if (parseInt(rInValue.value) % 10 == 0) {
            calculatedRout = parseInt(rInValue.value) + 10;
        } else {
            calculatedRout = parseInt(rInValue.value) + 1;
        }
        rOutValue.value = calculatedRout > 100 ? 100 : calculatedRout;
        rOut.value = rOutValue.value;
    }
    if (inputField == 'rOut') {
        if (rOut.value <= parseInt(Math.floor(parseInt(rInValue.value) / 10) * 10)) {
            rOut.value = parseInt(Math.floor(parseInt(rInValue.value) / 10) * 10) + 10;
            console.log(parseInt(Math.floor(parseInt(rInValue.value) / 10) * 10))
        }
        if (rOut.value >= 100) {
            rOut.value = 100;
            rOutValue.value = 100;
        }
        rOutValue.value = rOut.value;
    }
    if (inputField == 'rOutValue') {
        if (rOutValue.value <= parseInt(rInValue.value)) {
            rOutValue.value = parseInt(rInValue.value) + 1;
        }
        if (rOutValue.value >= 100) {
            rOutValue.value = 100;
            rOut.value = 100;
        }
        rOut.value = rOutValue.value;
    }
}

function toggleFilterInput(mode) {
    if (mode === 'errorAll') {
        document.getElementById('filterGroup').style.display = 'none';
    } else if (mode === 'errorFilter') {
        document.getElementById('filterGroup').style.display = 'block';
    }
    updateURLParams();
}

function toggleRangeInput(mode) {
    if (mode === 'r_in') {
        document.getElementById('rInGroup').style.display = 'block';
        document.getElementById('rOutGroup').style.display = 'none';
    } else if (mode === 'r_out') {
        document.getElementById('rInGroup').style.display = 'none';
        document.getElementById('rOutGroup').style.display = 'block';
    }
    updateURLParams();
}
// Function to update the URL query parameters
function updateURLParams() {
    document.querySelector("#loader").style.display = "block";
    const rIn = document.getElementById('rIn').value;
    const rOut = document.getElementById('rOut').value;
    const rInValue = document.getElementById('rInValue').value;
    const rOutValue = document.getElementById('rOutValue').value;
    // const errorData = document.querySelector('input[name="error"]:checked').value;
    const plotValue = document.querySelector('input[name="plot"]:checked').value;
    const rMode = document.querySelector('input[name="rMode"]:checked').value;

    // Update the URL with the new query parameters
    // const newURL = window.location.origin + window.location.pathname + `?rIn=${rInValue}&rOut=${rOutValue}&error=${errorValue}&plot=${plotValue}`;
    // window.history.pushState({path: newURL}, '', newURL);
    // Construct the data object to send to the Flask backend
    const data = {
        "rIn": rIn,
        "rOut": rOut,
        "rInValue": rInValue,
        "rOutValue": rOutValue,
        "plot": plotValue,
        "rMode": rMode
    };

    // Make an AJAX request to the Flask backend to update the parameters
    fetch('/matrix', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        window.location.reload();
        document.querySelector("#loader").style.display = "none";
    })
}

// Add event listeners to the error and plot selection radio buttons
const errorRadios = document.querySelectorAll('input[name="error"]');
errorRadios.forEach(radio => {
    radio.addEventListener('change', updateURLParams);
});

const plotRadios = document.querySelectorAll('input[name="plot"]');
plotRadios.forEach(radio => {
    radio.addEventListener('change', updateURLParams);
});