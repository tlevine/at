from datetime import datetime

#@app.template_filter('strfts')
def strfts(ts, format='%d/%m/%Y %H:%M'):
    return datetime.fromtimestamp(ts).strftime(format)
