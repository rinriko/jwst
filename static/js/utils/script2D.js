function updateRangInput(inputField) {
    var rIn = document.getElementById('rIn');
    var rInValue = document.getElementById('rInValue');
    var rOut = document.getElementById('rOut');
    var rOutValue = document.getElementById('rOutValue');
    var noOfBins = document.getElementById('noOfBins');
    var noOfBinsValue = document.getElementById('noOfBinsValue');
    var noOfDataPoint = document.getElementById('noOfDataPoint');
    var noOfDataPointValue = document.getElementById('noOfDataPointValue');
    var mode = document.getElementById('mode').value;
    if (mode == 'compare') {
        if (inputField == 'rIn') {
            if (rIn.value <= 10) {
                rIn.value = 10;
                rInValue.value = 10;
            }
            if (rIn.value >= 90) {
                rIn.value = 90;
                rInValue.value = 90;
            }
            rInValue.value = rIn.value
        }
        if (inputField == 'rInValue') {
            if (rInValue.value <= 10) {
                rIn.value = 10;
                rInValue.value = 10;
            }
            if (rInValue.value >= 90) {
                rIn.value = 90;
                rInValue.value = 90;
            }
            rIn.value = rInValue.value;
        }
        if (inputField == 'rOut') {
            if (rOut.value <= 20) {
                rOut.value = 20;
                rOutValue.value = 20;
            }
            if (rOut.value >= 100) {
                rOut.value = 100;
                rOutValue.value = 100;
            }
            rOutValue.value = rOut.value;
        }
        if (inputField == 'rOutValue') {
            if (rOutValue.value <= 20) {
                rOutValue.value = 20;
                rOut.value = 20;
            }
            if (rOutValue.value >= 100) {
                rOutValue.value = 100;
                rOut.value = 100;
            }
            rOut.value = rOutValue.value;
        }


    } else if (mode == 'custom') {
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


    if (inputField == 'noOfBins') {
        noOfBinsValue.value = noOfBins.value;
    }
    if (inputField == 'noOfBinsValue') {
        noOfBins.value = noOfBinsValue.value;
    }
    if (inputField == 'noOfDataPoint') {
        noOfDataPointValue.value = noOfDataPoint.value;
    }
    if (inputField == 'noOfDataPointValue') {
        noOfDataPoint.value = noOfDataPointValue.value;
    }
}

function toggleMode(mode) {
    if (mode === 'compare') {
        document.getElementById("configureTitle").textContent = "Configure Compare Data";
        document.getElementById("configureLabel").textContent = "Compare using constant:";
        document.getElementById('compareGroup').style.display = 'block';
        toggleRangeInput(document.querySelector('input[name="rMode"]:checked').value);
    } else if (mode === 'custom') {
        document.getElementById("configureTitle").textContent = "Configure Custom Data";
        document.getElementById("configureLabel").textContent = "Custom radian value:";
        document.getElementById('compareGroup').style.display = 'none';
        document.getElementById('rInGroup').style.display = 'block';
        document.getElementById('rOutGroup').style.display = 'block';
        updateRangInput('rIn');
    } else if (mode === 'average') {
        var xAxis = document.getElementById('xAxis').value;
        document.getElementById('avgGroup').style.display = 'block';
        if (xAxis == 'phase') {
            document.getElementById('avgGroup1').style.display = 'block';
            document.getElementById('avgGroup2').style.display = 'none';
        } else {
            document.getElementById('avgGroup1').style.display = 'none';
            document.getElementById('avgGroup2').style.display = 'block';
        }
    } else if (mode === 'raw') {
        document.getElementById('avgGroup').style.display = 'none';
    } else if (mode === 'r_in') {
        document.getElementById('rInGroup').style.display = 'block';
        document.getElementById('rOutGroup').style.display = 'none';
    } else if (mode === 'r_out') {
        document.getElementById('rInGroup').style.display = 'none';
        document.getElementById('rOutGroup').style.display = 'block';
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
    const r_in = document.getElementById('rIn').value;
    const r_out = document.getElementById('rOut').value;
    const mode = document.getElementById('mode').value;
    const noOfBins = document.getElementById('noOfBins').value;
    const noOfDataPoint = document.getElementById('noOfDataPoint').value;
    const rMode = document.querySelector('input[name="rMode"]:checked').value;
    const dataType = document.getElementById('dataType').value;
    const errorBars = document.getElementById('errorBars').value;
    const plotType = document.getElementById('plotType').value;
    const xAxis = document.getElementById('xAxis').value;

    document.getElementById('title1').innerText = "ZTF J1539 PSF Light Curves - " + document.getElementById('mode').options[document.getElementById('mode').selectedIndex].text;

    var data = {
        "r_in": r_in,
        "r_out": r_out,
        "mode": mode,
        "errorBars": errorBars,
        "plotType": plotType,
        "dataType": dataType,
        "rMode": rMode,
        "xAxis": xAxis,
        "noOfBins": noOfBins,
        "noOfDataPoint": noOfDataPoint,
    };
    console.log(data)
    socket.emit('requestGraphUpdate', data);
}
