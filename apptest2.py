import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import msal

# Microsoft Graph API credentials
client_id = 's3h8Q~J6g_lGDn0qHXoaCDV_9UU9JCmrFUwvYduo'
tenant_id = '178a51bf-8b20-49ff-b655-56245d5c173c'
client_secret = '49126ca7-877a-4492-8d7d-1d2f0a0e5d11'
authority_url = f'https://login.microsoftonline.com/{tenant_id}'
folder_path = "/personal/phornsawan_roemsri_ttu_edu/Documents/Documents/Paper Dr.Dang/jwst/img/full-size/epoch1/lw"

# Function to get access token
def get_access_token():
    client = msal.ConfidentialClientApplication(
        client_id,
        authority=authority_url,
        client_credential=client_secret
    )
    token = client.acquire_token_for_client(scopes=["Files.Read.All", "Files.ReadWrite.All"])
    print(token)
    return token['access_token'] if "access_token" in token else None

# Function to list files in OneDrive folder
def list_files(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"
    response = requests.get(url, headers=headers)
    print(url)
    
    if response.status_code == 200:
        return response.json().get('value', [])
    else:
        return []

# Create the Dash app
app = dash.Dash(__name__)

# Layout of the Dash app
app.layout = html.Div([
    html.H1("OneDrive Image Viewer"),
    html.Button('Load Images', id='load-images-btn', n_clicks=0),
    html.Div(id='file-list'),
    html.Div(id='image-container', children=[
        html.Img(id='display-image', style={'max-width': '100%'})
    ])
])

# Callback to load and display files from OneDrive
@app.callback(
    Output('file-list', 'children'),
    [Input('load-images-btn', 'n_clicks')]
)
def display_files(n_clicks):
    if n_clicks > 0:
        access_token = get_access_token()
        files = list_files(access_token)
        if files:
            # Display file links
            return html.Ul([
                html.Li(
                    html.A(file['name'], href='#', id={'type': 'file-link', 'index': i}),
                    style={'cursor': 'pointer'}
                )
                for i, file in enumerate(files)
            ])
        return html.Div("No files found.")
    return html.Div("Click 'Load Images' to fetch files from OneDrive.")

# Callback to display selected image
@app.callback(
    Output('display-image', 'src'),
    [Input({'type': 'file-link', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [dash.dependencies.State('file-list', 'children')]
)
def display_image(n_clicks, file_list):
    if n_clicks and any(n_clicks):
        # Find the clicked link and get file URL
        clicked_idx = [i for i, click in enumerate(n_clicks) if click][0]
        access_token = get_access_token()
        files = list_files(access_token)
        file_url = files[clicked_idx]['@microsoft.graph.downloadUrl']
        return file_url
    return ""

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
