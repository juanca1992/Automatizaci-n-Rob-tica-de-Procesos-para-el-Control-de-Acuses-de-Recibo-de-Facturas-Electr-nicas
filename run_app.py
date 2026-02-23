from main import app
import uvicorn
import webbrowser

webbrowser.open('http://127.0.0.1:8000/docs')



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

'''
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''