#!/usr/bin/python3

import argparse
import cec
import logging
import uvicorn
from fastapi import FastAPI, Body, Path
from fastapi.responses import RedirectResponse

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="CEC REST API", description="REST API to control HDMI devices via the CEC protocol", version="1.0")
app.state.cecadapter = None
app.state.status = {}

@app.on_event("startup")
async def app_startup():
  cec_init()
  cec_transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_GIVE_DEVICE_POWER_STATUS)

@app.on_event("shutdown")
async def app_shutdown():
  cec_close()

@app.get("/", include_in_schema=False)
async def home_page():
  return RedirectResponse("/docs")

@app.get("/health", tags=["health"])
async def health():
  return {"status": "UP"}

@app.get("/device/{device}/status", tags=["devices"])
async def get_device_status(device: int = Path(ge=0, le=11)):
  if device in app.state.status:
    return app.state.status[device]
  else:
    return 0

@app.put("/device/{device}/status", tags=["devices"])
async def set_device_status(device: int = Path(ge=0, le=11), status: int = Body()):
  if status > 0:
    app.state.status[device] = 1
    cec_transmit(device, cec.CEC_OPCODE_IMAGE_VIEW_ON)
  else:
    app.state.status[device] = 0
    cec_transmit(device, cec.CEC_OPCODE_STANDBY)
  logger.info("Device {} status: {}".format(device, app.state.status[device]))
  return {"message": "Device {} status changed to {}".format(device, app.state.status[device])}

def cec_init():
  app.state.cecconfig = cec.libcec_configuration()
  app.state.cecconfig.strDeviceName = app.title
  app.state.cecconfig.bActivateSource = 0
  app.state.cecconfig.bMonitorOnly = 1
  app.state.cecconfig.deviceTypes.Add(cec.CEC_DEVICE_TYPE_RECORDING_DEVICE)
  app.state.cecconfig.clientVersion = cec.LIBCEC_VERSION_CURRENT
  app.state.cecconfig.SetLogCallback(cec_log_callback)
  app.state.cecconfig.SetCommandCallback(cec_command_callback)
  app.state.cecadapter = cec.ICECAdapter.Create(app.state.cecconfig)
  logger.debug("libCEC version %s loaded: %s", app.state.cecadapter.VersionToString(app.state.cecconfig.serverVersion), app.state.cecadapter.GetLibInfo())
  adapters = app.state.cecadapter.DetectAdapters()
  for adapter in adapters:
    logger.info("Found a CEC adapter on port: %s", adapter.strComName)
    if app.state.cecadapter.Open(adapter.strComName):
      return
    else:
      raise Exception("Failed to open a connection to the CEC adapter")
  raise Exception("No CEC adapters found")

def cec_transmit(device, opcode):
  cmd = cec.cec_command()
  cec.cec_command.Format(cmd, cec.CECDEVICE_BROADCAST, device, opcode)
  if not app.state.cecadapter.Transmit(cmd):
    logger.error("Failed to send CEC command")

def cec_close():
  if app.state.cecadapter is not None:
    app.state.cecadapter.Close()

def cec_log_callback(level, time, message):
  if level == cec.CEC_LOG_ERROR:
    logger.error("CEC: " + message)
  elif level == cec.CEC_LOG_WARNING:
    logger.warning("CEC: " + message)
  elif level == cec.CEC_LOG_NOTICE:
    logger.info("CEC: " + message)
  elif level == cec.CEC_LOG_TRAFFIC:
    logger.debug("CEC: " + message)
  elif level == cec.CEC_LOG_DEBUG:
    logger.debug("CEC: " + message)
  return 0

def cec_command_callback(cmd):
  parsed = app.state.cecadapter.CommandFromString(cmd)
  if parsed.opcode == cec.CEC_OPCODE_REQUEST_ACTIVE_SOURCE:
    app.state.status[parsed.initiator] = 1
  elif parsed.opcode == cec.CEC_OPCODE_STANDBY:
    app.state.status[parsed.initiator] = 0
  elif parsed.opcode == cec.CEC_OPCODE_REPORT_POWER_STATUS:
    status = parsed.parameters.At(0)
    if status == cec.CEC_POWER_STATUS_ON or status == cec.CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON:
      app.state.status[parsed.initiator] = 1
    elif status == cec.CEC_POWER_STATUS_STANDBY or status == cec.CEC_POWER_STATUS_IN_TRANSITION_ON_TO_STANDBY:
      app.state.status[parsed.initiator] = 0
  logger.info("Device {} status: {}".format(parsed.initiator, app.state.status[parsed.initiator]))
  return 0

def parse_args():
  parser = argparse.ArgumentParser(description=app.title)
  parser.add_argument("-a", "--address", help="Address to bind to", type=str, default="127.0.0.1")
  parser.add_argument("-p", "--port", help="Port to listen on", type=int, default=8000)
  parser.add_argument("-l", "--log-level", help="Log level", type=str, default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"])
  return parser.parse_args()

def main():
  args = parse_args()
  uvicorn.run(app, host=args.address, port=args.port, log_level=logging.getLevelName(args.log_level))

if __name__ == "__main__":
  main()
