import subprocess
import traceback
import PySimpleGUI as sg
from findFiles import findFiles


def progressWindow(
    pidList,
    # findFiles,
    backlog,
    transcode,
    transferToServer,
    moveDirsToConverted,
    transferFilesToServer,
    acceptedFileTypes,
    replaceVideoArgs,
    videoArgs,
    audioArgs,
    pixelFormat,
    subtitles,
    replaceAudioArgs,
    dirs,
    dirsToConvert,
):
    transcodesDone = 0
    notStartedFindFiles = True

    layout = [
        [sg.Text(text="Transcoding files...")],
        [sg.ProgressBar(max_value=1, key="progressBar", size=(100, 20))],
        [sg.Text(key="displayText")],
        [sg.Button(button_text="Cancel", key="Cancel", enable_events=True)],
    ]

    window = sg.Window(
        title="Transcoding files", layout=layout, margins=(20, 20), finalize=True
    )
    progressbar = window["progressBar"]

    try:
        window.write_event_value("Start", None)
        while True:
            event = window.read()[0]

            if "movingFiles:" in event:
                window["displayText"].update(("moving: " + event.split(":")[1]))

            if event in (None, "Cancel") or event == sg.WIN_CLOSED or "Exit" in event:
                for pid in pidList:
                    subprocess.Popen(
                        "TASKKILL /PID " + str(pid) + " /F /T",
                        shell=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                if "TransfersDone" in event:
                    sg.popup(
                        "Done with transcoding and Transfering files!",
                        "transcoded and transfered " + str(transcodesDone) + " files.",
                    )

                window.close()
                break

            elif event == "Start" and notStartedFindFiles:
                findFiles(
                    window,
                    acceptedFileTypes,
                    replaceVideoArgs,
                    videoArgs,
                    audioArgs,
                    pixelFormat,
                    subtitles,
                    replaceAudioArgs,
                    backlog,
                    dirs,
                    dirsToConvert,
                )
                notStartedFindFiles = False

            elif event == "-filesFound-":
                window["progressBar"].UpdateBar(transcodesDone, len(backlog))
                transcode(
                    window=window,
                    transcodeCommand=str(backlog[transcodesDone]["transcodeCommand"]),
                    finalName=str(backlog[transcodesDone]["finalName"]),
                    fileDir=str(backlog[transcodesDone]["fileDir"]),
                )

            elif "-TRANSCODE-" in event:
                if "transcodeDone" in event:
                    transcodesDone += 1
                    progressbar.UpdateBar(transcodesDone)

                if transcodesDone == len(backlog) or len(backlog) == 1:

                    if transferToServer:
                        window.perform_long_operation(moveDirsToConverted, "Transfer")

                    else:
                        sg.popup(
                            "Done with transcoding!",
                            "transcoded " + str(transcodesDone) + " files.",
                        )
                        window.write_event_value("Exit", None)
                else:
                    transcode(
                        window=window,
                        transcodeCommand=str(
                            backlog[transcodesDone]["transcodeCommand"]
                        ),
                        finalName=str(backlog[transcodesDone]["finalName"]),
                        fileDir=str(backlog[transcodesDone]["fileDir"]),
                    )

            elif event == "Transfer" and transferToServer:
                window.perform_long_operation(
                    lambda: transferFilesToServer(window=window), "Exit TransfersDone"
                )

    except Exception as e:
        tb = traceback.format_exc()
        sg.Print(f"An error has occured. here is info: ", e, tb)
        sg.popup_error(f"AN EXCEPTION OCCURRED!", e, tb)
