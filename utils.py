import requests
from pathlib import Path
import re

# sidebar
def url_exists(url: str, timeout: float = 5.0) -> bool:
    """
    Returns True if the URL returns a 200-level status code.
    Uses HEAD first, falls back to GET if HEAD is not allowed.
    """
    try:
        # Try a HEAD first (lighter than GET)
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code == 405:
            # Some servers disallow HEAD – fall back to GET without downloading the body
            resp = requests.get(url, stream=True, timeout=timeout)
        return 200 <= resp.status_code < 300
    except requests.RequestException:
        return False
    

# content
# Extract epoch information and sort points accordingly
def extract_epoch(filename):
    match = re.search(r"epoch(\d+)", filename)
    if match:
        return int(match.group(1))  # Extract numeric epoch if found
    # Use infinity if no epoch is found, so it sorts last
    return float('inf')

def process_points(pt, type, tooltipFontSize, thumnailsSize, dataSelection, annotation):
    children = []
    img_data = {}
    imglist = []
    bbox = pt.get("bbox", None)
    curveNumber = pt.get("curveNumber", None)
    pointIndex = pt.get("pointIndex", None)
    customdata = pt["customdata"]
    phase, wavetype = customdata.get("phase"), customdata.get("type")
    phase, wavetype, r_in, r_out = customdata.get("phase"), customdata.get(
        "type"), customdata.get("r_in"), customdata.get("r_out")
    # fig_anno_index = f"{wavetype}_{phase}"
    # point_index = f"c{curveNumber}pid{pointIndex}"
    point_index = f"{wavetype}_{phase}"
    # point_index = f"{wavetype}_{phase}_{r_in}_{r_out}"

    if "datatype" in customdata:
        return False, bbox, []

    img_src = f"https://via.placeholder.com/150?text={'Not exist'}"
    if "filename" in customdata:
        filename = customdata["filename"]
        # Extract values, ensuring they are properly formatted
        y_value = pt.get("y", "N/A")
        mjd_value = customdata.get("mjd", "N/A")
        time_value = customdata.get("time", "N/A")
        phase_value = customdata.get("phase", "N/A")
        wavetype = customdata.get("type", "N/A")
        # Create a formatted string for each
        y_text = f'Y-Axis: {y_value:,.5f}'
        mjd_text = f'MJD: {mjd_value:,.5f}' if isinstance(
            mjd_value, (float, int)) else f'MJD: {mjd_value}'
        time_text = f'Time: {time_value}'
        phase_text = f'Phase: {phase_value:,.3f}' if isinstance(
            phase_value, (float, int)) else f'Phase: {phase_value}'
        color = color_list[(curveNumber % len(
            dataSelection)) % len(color_list)]
        # Combine the paths
        file_path = f"{config.IMG_URI}{filename}"
        # print(file_path)
        # Check if the file exists
        if filename not in imglist:
            imglist.append(filename)
            if Path(file_path).exists():
                img_src = file_path
            elif url_exists(file_path):
                img_src = file_path
            else:
                img_src = None

            img_data[img_src] = {
                'img_src': img_src,
                'mjd_text': mjd_text,
                'time_text': time_text,
                'type': wavetype,
                'phase_value': phase_value,
                'phase_text': phase_text,
                'point_index': point_index,
                'customdata': customdata,
                'filename': customdata.get('filename', 'N/A')
            }
        else:
            img_src = None

        if type == 'hover':
            fontSize = f'{tooltipFontSize}px'
            wh = f'{thumnailsSize}px'
            whd = 150
            if int(tooltipFontSize) >= 18:
                whd = 200
            if int(tooltipFontSize) >= 24:
                whd = 250
            if int(tooltipFontSize) >= 30:
                whd = 300
            whdiv = f'{whd}px'

            # Adjust sizes and spacing for a more compact layout
            children.append(
                html.Div([
                    # Smaller image or space
                    html.Img(src=img_src, style={
                        "width": wh, "height": wh, "objectFit": "cover"}) if img_src else html.Br(),
                    html.Div([
                        html.Span(style={"backgroundColor": color, "borderRadius": "50%",
                                         "display": "inline-block", "width": "8px", "height": "8px", "marginRight": "5px"}),
                        html.Div([
                            html.P(y_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),  # Smaller text
                            html.P(mjd_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),
                            html.P(time_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),
                            html.P(phase_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize})
                        ], style={"display": "flex", "flexDirection": "column", "justifyContent": "center"})
                    ], style={"display": "flex", "alignItems": "center"})
                ], style={'width': whdiv, 'white-space': 'normal', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            )
    if type == 'click':
        # print(annotation)
        # Create children elements based on the grouped data
        for img_src, data in img_data.items():
            mjd_text = data['mjd_text']
            time_text = data['time_text']
            wavetype = data['type']
            phase_value = data['phase_value']
            phase_text = data['phase_text']
            point_index = data['point_index']
            customdata = data['customdata']
            customdata_json = json.dumps(customdata)
            children.append(
                html.Div([
                            html.Button(DashIconify(icon="clarity:trash-line", width=20), id={'type': 'delete-btn', 'index': point_index}, n_clicks=0,
    style={
        'background-color': 'orange',
        'color': 'black',
        'border': 'none',
        'cursor': 'pointer',
        'position': 'absolute',
        'top': '5px',
        'right': '5px',
        'display': 'flex',  # Use flexbox for alignment
        'align-items': 'center',  # Center vertically
        'justify-content': 'center',  # Center horizontally
        'width': '30px',  # Set a specific width if necessary
        'height': '30px',  # Set a specific height if necessary
        'border-radius': '10%',
    }),
                    # html.Button('×', id={'type': 'delete-btn', 'index': point_index}, n_clicks=0, style={'background-color': '#FF8700',
                    #             'color': 'white', 'border': 'none', 'cursor': 'pointer', 'position': 'absolute', 'top': '5px', 'right': '5px'}),
                    html.Div(
                        annotation['text'],
                        style={
                            'position': 'absolute',
                            'top': '5px',  # Adjust as needed
                            'left': '5px',  # Adjust as needed
                            # Semi-transparent background
                            'background-color': 'rgba(0, 0, 0, 1)',
                            # 'background-color': 'rgba(0, 0, 0, 0.5)',
                            'color': 'white',
                            'padding': '2px 5px',
                            'border-radius': '3px',
                            'font-size': '12px',
                            'font-weight': 'bold'
                        }
                    ),
                    html.Img(
                        src=img_src,
                        style={'width': '150px', 'height': '150px',
                               'margin': '5px', 'cursor': 'pointer'},
                        id={'type': 'dynamic-img',
                            'index': point_index, 'src': img_src}
                    )
                ], style={'position': 'relative'},
                    id={'type': 'dynamic-div-img', 'index': point_index},
                    # Adding custom data attributes here
                    **{
                    'data-mjd-text': mjd_text,
                    'data-time-text': time_text,
                    'data-phase-value': phase_value,
                    'data-wave-type': wavetype,
                    'data-phase-text': phase_text,
                    'data-filename': customdata.get('filename', 'N/A'),
                    'data-img-src': img_src,
                    'data-point-index': point_index,
                    'data-customdata': customdata_json,
                }
                )
            )
    return True, bbox, children
