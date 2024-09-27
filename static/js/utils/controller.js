// Get references to elements
const controlPanel = document.getElementById('controlPanel');
const burgerMenu = document.getElementById('burgerMenu');
const content = document.getElementById('content');
const rIn = document.getElementById('rIn');
const rOut = document.getElementById('rOut');
const noOfBins = document.getElementById('noOfBins');
const noOfDataPoint = document.getElementById('noOfDataPoint');
// Toggle the content visibility
function toggleContent() {
    content.classList.toggle('content-hidden');
    // Toggle the width and border-radius for circle shape
    if (content.classList.contains('content-hidden')) {
        console.log("content-hidden")
        controlPanel.style.width = 'calc(2rem + 0.9vw)';
        controlPanel.style.height = 'calc(2rem + 0.9vw)';
        burgerMenu.style.top = '50%';
        burgerMenu.style.right = '50%';
        controlPanel.style.borderRadius = '50%';
        controlPanel.style.backgroundColor = '#e6fefb';
        // controlPanel.style.lineHeight = '50px';
        // controlPanel.style.fontSize = '50px';
    } else {
        controlPanel.style.width = '250px';
        controlPanel.style.height = 'auto';
        controlPanel.style.borderRadius = '8px';
        controlPanel.style.backgroundColor = '#e6fefb';
        burgerMenu.style.top = '5%';
        burgerMenu.style.right = '10%';
        // Check and adjust position to keep it within the viewport
        let rect = controlPanel.getBoundingClientRect();
        if (rect.left + rect.width > window.innerWidth) {
            controlPanel.style.left = window.innerWidth - rect.width + 'px';
        }
        if (rect.top + rect.height > window.innerHeight) {
            controlPanel.style.top = window.innerHeight - rect.height + 'px';
    }
    }

}
// toggleContent()
// Make the control panel draggable
let isDragging = false;
let isRageFocus = false;
let offsetX, offsetY;

controlPanel.addEventListener('mousedown', (e) => {
    isDragging = true;
    offsetX = e.clientX - controlPanel.getBoundingClientRect().left;
    offsetY = e.clientY - controlPanel.getBoundingClientRect().top;
});

rIn.addEventListener('mousedown', (e) => {
    isRageFocus = true
});
rOut.addEventListener('mousedown', (e) => {
    isRageFocus = true
});
noOfBins.addEventListener('mousedown', (e) => {
    isRageFocus = true
});
noOfDataPoint.addEventListener('mousedown', (e) => {
    isRageFocus = true
});

document.addEventListener('mousemove', (e) => {
    if (isRageFocus) {
        isDragging = false;
    } else {
        if (isDragging) {      
            let newLeft = e.clientX - offsetX;
            let newTop = e.clientY - offsetY;
            // Check left boundary
            if (newLeft < 0) {
                newLeft = 0;
            } else if (newLeft + controlPanel.offsetWidth > window.innerWidth) {
                newLeft = window.innerWidth - controlPanel.offsetWidth;
            }
            // Check top boundary
            if (newTop < 0) {
                newTop = 0;
            } else if (newTop + controlPanel.offsetHeight > window.innerHeight) {
                newTop = window.innerHeight - controlPanel.offsetHeight;
            }
            controlPanel.style.left = newLeft + 'px';
            controlPanel.style.top = newTop + 'px';
        }
    }
});

document.addEventListener('mouseup', () => {
    isDragging = false;
    isRageFocus = false;
});