import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import flatdict
import pprint
import datetime
import time


class mygsheet:
    def __init__(self) -> None:
        # pass
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scopes)
        client = gspread.authorize(creds)
        self.sheet = client.open("test-abrp").sheet1
        self.mydata = {}

    def update_mysheet(self):
        # abrp=['''=INDIRECT("B"&LIGNE())/86400+DATE(1970;1;1)+TEMPS(1;0;0)''']
        abrp = []
        data = self.mydata
        dict = [
            "soc",
            "soc_kwh",
            "power",
            "voltage",
            "current",
            "is_charging",
            "target_soc",
            "is_parked",
            "ext_temp",
            "odometer",
            "speed",
            "est_battery_range",
            "battery_voltage",
            #     # 'bmsReserCtrlDspCmd' ,
            #     # 'bmsReserStHourDspCmd' ,
            #     # 'bmsReserStMintueDspCmd',
            #     # 'bmsReserSpHourDspCmd' ,
            #     # 'bmsReserSpMintueDspCmd'  ,
            #     # 'bmsOnBdChrgTrgtSOCDspCmd' ,
            # # NOT KNOW    'bms_estd_elec_rng'  ,
            #     'bmsAltngChrgCrntDspCmd'  ,
            #     'bmsChrgCtrlDspCmd' ,
            #     'chrgngRmnngTime' ,
            #     'chrgngRmnngTimeV' ,
            #     'bmsChrgOtptCrntReq'  ,
            # # NOT KNOW    'bmsChrgOtptCrntReqV'  ,
            #     'bmsPackCrnt'  ,
            #     # 'bmsPackCrntV'  ,
            #     'bmsPackVol' ,
            #     'bmsPackSOCDsp'  ,
            #     'bmsChrgSts'  ,
            #     # 'bmsChrgSpRsn'  ,
            #     'clstrElecRngToEPT'  ,
            #     'bmsPTCHeatReqDspCmd' ,
            #     'bmsPTCHeatResp'  ,
            #     'ccuEleccLckCtrlDspCmd'  ,
            #     'bmsPTCHeatSpRsn' ,
            # # NOT KNOW    'bmsDsChrgSpRsn'  ,
            # # NOT KNOW    'disChrgngRmnngTime'  ,
            # # NOT KNOW    'disChrgngRmnngTimeV'  ,
            #     # 'imcuVehElecRng' ,
            #     # 'imcuVehElecRngV'  ,
            #     # 'imcuChrgngEstdElecRng'  ,
            #     # 'imcuChrgngEstdElecRngV'  ,
            # # NOT KNOW    'imcuDschrgngEstdElecRng'  ,
            #     # 'imcuDschrgngEstdElecRngV'  ,
            #     # 'chrgngSpdngTime' ,
            #     # 'chrgngSpdngTimeV'  ,
            #     # 'chrgngAddedElecRng'  ,
            #     # 'chrgngAddedElecRngV'  ,
            # # NOT KNOW    'onBdChrgrAltrCrntInptCrnt'  ,
            # # NOT KNOW    'onBdChrgrAltrCrntInptVol'  ,
            # # NOT KNOW    'ccuOnbdChrgrPlugOn'  ,
            # # NOT KNOW    'ccuOffBdChrgrPlugOn'  ,
            #     # 'chrgngDoorPosSts'  ,
            #     # 'chrgngDoorOpenCnd'  ,
            #     # # '':charge_status.chargeStatus ,
            #     # # '':charge_status.chargeStatus.init_from_dict(data.get('chargeStatus'))
            #     # 'bmsAdpPubChrgSttnDspCmd'
        ]

        # print(type(data["utc"]))

        date_time = datetime.datetime.fromtimestamp(
            data["utc"], tz=pytz.timezone("Europe/Paris")
        )
        datesheet = date_time.strftime("%d/%m/%Y %H:%M:%S")
        abrp.append(datesheet)
        for dico in dict:
            empty = False
            # print(dico, data[dico])
            if data["est_battery_range"] > 500:
                empty = True
            if data["soc"] > 100:
                empty = True
            if empty:
                abrp.append("")
            else:
                abrp.append(data[dico])

        # self.sheet.append_row(abrp, table_range="A2", value_input_option='USER_ENTERED')
        self.sheet.insert_row(
            abrp, index=2, value_input_option="USER_ENTERED", inherit_from_before=False
        )

    def save_mydata(self, status, charge_status):
        # if charge_status.chrgMgmtData.decoded_current!=0 \
        # or status.is_charging==1:
        if status.basicVehicleStatus.engineStatus or status.basicVehicleStatus.extendedData2 or status.basicVehicleStatus.remoteClimateStatus > 0:
            self.mydata.update(
                {
                    "utc": int(
                        time.time()
                    ),  # We assume the timestamp is now, we will update it later from GPS if available
                    # 'is_charging': status.is_charging,
                    "is_charging": status.basicVehicleStatus.extendedData2,
                    # 'is_parked': status.is_parked,
                    "is_parked": "True" if status.gpsPosition.wayPoint.speed==0 else "False",
                    "soc": (charge_status.chrgMgmtData.bmsPackSOCDsp / 10.0),
                    "power": round(charge_status.chrgMgmtData.decoded_power, 3),
                    "voltage": round(charge_status.chrgMgmtData.decoded_voltage, 3),
                    "current": round(charge_status.chrgMgmtData.decoded_current, 3),
                    # LBR
                    "target_soc": (
                        charge_status.chrgMgmtData.charge_target_soc.percentage
                    ),
                    "ext_temp": status.basicVehicleStatus.exteriorTemperature,
                    "odometer": status.basicVehicleStatus.mileage / 10.0,
                    "speed": status.gpsPosition.wayPoint.speed / 10.0,
                    "est_battery_range": float(status.basicVehicleStatus.fuelRangeElec)
                    / 10.0,
                    "heading": status.gpsPosition.wayPoint.heading,
                    "battery_voltage": float(status.basicVehicleStatus.batteryVoltage)
                    / 10.0,
                    "lat": status.gpsPosition.wayPoint.position.latitude
                    / 1000000.000000,
                    "lon": status.gpsPosition.wayPoint.position.longitude
                    / 1000000.000000,
                    "elevation": status.gpsPosition.wayPoint.position.altitude,
                    "soc_kwh": int(
                        (charge_status.rvsChargeStatus.realtimePower * 640) / 725
                    )
                    / 10.0,
                    #     # charge_status.bmsAdpPubChrgSttnDspCmd,
                    #     # charge_status.bmsAltngChrgCrntDspCmd,
                    #     # charge_status.bmsChrgCtrlDspCmd ,
                    #     # charge_status.bmsChrgOtptCrntReq ,
                    #     # charge_status.bmsChrgOtptCrntReqV ,
                    #     # charge_status.bmsChrgSpRsn ,
                    #     # 'bmsReserCtrlDspCmd':charge_status.bmsReserCtrlDspCmd ,
                    #     # 'bmsReserStHourDspCmd':charge_status.bmsReserStHourDspCmd ,
                    #     # 'bmsReserStMintueDspCmd':charge_status.bmsReserStMintueDspCmd ,
                    #     # 'bmsReserSpHourDspCmd':charge_status.bmsReserSpHourDspCmd ,
                    #     # 'bmsReserSpMintueDspCmd':charge_status.bmsReserSpMintueDspCmd ,
                    #     # 'bmsOnBdChrgTrgtSOCDspCmd':charge_status.bmsOnBdChrgTrgtSOCDspCmd ,
                    # # NOT KNOW    'bms_estd_elec_rng':charge_status.chrgMgmtData.bms_estd_elec_rng ,
                    #     'bmsAltngChrgCrntDspCmd':charge_status.chrgMgmtData.bmsAltngChrgCrntDspCmd ,
                    #     'bmsChrgCtrlDspCmd':charge_status.chrgMgmtData.bmsChrgCtrlDspCmd ,
                    #     'chrgngRmnngTime':charge_status.chrgMgmtData.chrgngRmnngTime ,
                    #     'chrgngRmnngTimeV':charge_status.chrgMgmtData.chrgngRmnngTimeV ,
                    #     'bmsChrgOtptCrntReq':charge_status.chrgMgmtData.bmsChrgOtptCrntReq ,
                    # # NOT KNOW    'bmsChrgOtptCrntReqV':charge_status.chrgMgmtData.bmsChrgOtptCrntReqV ,
                    #     'bmsPackCrnt':charge_status.chrgMgmtData.bmsPackCrnt ,
                    #     # 'bmsPackCrntV':charge_status.bmsPackCrntV ,
                    #     'bmsPackVol':charge_status.chrgMgmtData.bmsPackVol ,
                    #     'bmsPackSOCDsp':charge_status.chrgMgmtData.bmsPackSOCDsp ,
                    #     'bmsChrgSts':charge_status.chrgMgmtData.bmsChrgSts ,
                    #     # 'bmsChrgSpRsn':charge_status.bmsChrgSpRsn ,
                    #     'clstrElecRngToEPT':charge_status.chrgMgmtData.clstrElecRngToEPT ,
                    #     'bmsPTCHeatReqDspCmd':charge_status.chrgMgmtData.bmsPTCHeatReqDspCmd ,
                    #     'bmsPTCHeatResp':charge_status.chrgMgmtData.bmsPTCHeatResp ,
                    #     'ccuEleccLckCtrlDspCmd':charge_status.chrgMgmtData.ccuEleccLckCtrlDspCmd ,
                    #     'bmsPTCHeatSpRsn':charge_status.chrgMgmtData.bmsPTCHeatSpRsn ,
                    # # NOT KNOW    'bmsDsChrgSpRsn':charge_status.chrgMgmtData.bmsDsChrgSpRsn ,
                    # # NOT KNOW    'disChrgngRmnngTime':charge_status.chrgMgmtData.disChrgngRmnngTime ,
                    # # NOT KNOW    'disChrgngRmnngTimeV':charge_status.chrgMgmtData.disChrgngRmnngTimeV ,
                    #     # 'imcuVehElecRng':charge_status.imcuVehElecRng ,
                    #     # 'imcuVehElecRngV':charge_status.imcuVehElecRngV ,
                    #     # 'imcuChrgngEstdElecRng':charge_status.imcuChrgngEstdElecRng ,
                    #     # 'imcuChrgngEstdElecRngV':charge_status.imcuChrgngEstdElecRngV ,
                    # # NOT KNOW    'imcuDschrgngEstdElecRng':charge_status.chrgMgmtData.imcuDschrgngEstdElecRng ,
                    #     # 'imcuDschrgngEstdElecRngV':charge_status.imcuDschrgngEstdElecRngV ,
                    #     # 'chrgngSpdngTime':charge_status.chrgngSpdngTime ,
                    #     # 'chrgngSpdngTimeV':charge_status.chrgngSpdngTimeV ,
                    #     # 'chrgngAddedElecRng':charge_status.chrgngAddedElecRng ,
                    #     # 'chrgngAddedElecRngV':charge_status.chrgngAddedElecRngV ,
                    # # NOT KNOW    'onBdChrgrAltrCrntInptCrnt':charge_status.chrgMgmtData.onBdChrgrAltrCrntInptCrnt ,
                    # # NOT KNOW    'onBdChrgrAltrCrntInptVol':charge_status.chrgMgmtData.onBdChrgrAltrCrntInptVol ,
                    # # NOT KNOW    'ccuOnbdChrgrPlugOn':charge_status.chrgMgmtData.ccuOnbdChrgrPlugOn ,
                    # # NOT KNOW    'ccuOffBdChrgrPlugOn':charge_status.chrgMgmtData.ccuOffBdChrgrPlugOn ,
                    #     # 'chrgngDoorPosSts':charge_status.chrgngDoorPosSts ,
                    #     # 'chrgngDoorOpenCnd':charge_status.chrgngDoorOpenCnd ,
                    #     # # '':charge_status.chargeStatus ,
                    #     # # '':charge_status.chargeStatus.init_from_dict(data.get('chargeStatus'))
                    #     # 'bmsAdpPubChrgSttnDspCmd':charge_status.bmsAdpPubChrgSttnDspCmd
                }
            )
            self.update_mysheet()
            return True

        # flat_status =  flatdict.FlatDict((charge_status.chrgMgmtData.__dict__), delimiter='.')
        # pprint.pprint(dict(flat_status).items())
        # for k,v in dict(flat_status).items():print(k,':', v )
# 'bmsAdpPubChrgSttnDspCmd'
# 'bmsAltngChrgCrntDspCmd'
# 'bmsChrgCtrlDspCmd'
# 'bmsChrgOtptCrntReq'
# 'bmsChrgOtptCrntReqV'
# 'bmsChrgSpRsn'
# 'bmsChrgSts'
# 'bmsDsChrgSpRsn'
# 'bmsEstdElecRng'
# 'bmsOnBdChrgTrgtSOCDspCmd'
# 'bmsPackCrnt'
# 'bmsPackCrntV'
# 'bmsPackSOCDsp'
# 'bmsPackVol'
# 'bmsPTCHeatReqDspCmd'
# 'bmsPTCHeatResp'
# 'bmsPTCHeatSpRsn'
# 'bmsReserCtrlDspCmd'
# 'bmsReserSpHourDspCmd'
# 'bmsReserSpMintueDspCmd'
# 'bmsReserStHourDspCmd'
# 'bmsReserStMintueDspCmd'
# 'ccuEleccLckCtrlDspCmd'
# 'ccuOffBdChrgrPlugOn'
# 'ccuOnbdChrgrPlugOn'
# 'chrgngAddedElecRng'
# 'chrgngAddedElecRngV'
# 'chrgngDoorOpenCnd'
# 'chrgngDoorPosSts'
# 'chrgngRmnngTime'
# 'chrgngRmnngTimeV'
# 'chrgngSpdngTime'
# 'chrgngSpdngTimeV'
# 'clstrElecRngToEPT'
# 'disChrgngRmnngTime'
# 'disChrgngRmnngTimeV'
# 'imcuChrgngEstdElecRng'
# 'imcuChrgngEstdElecRngV'
# 'imcuDschrgngEstdElecRng'
# 'imcuDschrgngEstdElecRngV'
# 'imcuVehElecRng'
# 'imcuVehElecRngV'
# 'onBdChrgrAltrCrntInptCrnt'
# 'onBdChrgrAltrCrntInptVol'

        # flat_status =  flatdict.FlatDict((charge_status.rvsChargeStatus.__dict__), delimiter='.')
        # pprint.pprint(dict(flat_status).items())
        # for k,v in dict(flat_status).items():print(k,':', v )
# 'chargingDuration'
# 'chargingElectricityPhase'
# 'chargingGunState'
# 'chargingPileID'
# 'chargingPileSupplier'
# 'chargingType'
# 'endTime'
# 'extendedData1'
# 'extendedData2'
# 'extendedData3'
# 'extendedData4'
# 'fotaLowestVoltage'
# 'fuelRangeElec'
# 'lastChargeEndingPower'
# 'mileage'
# 'mileageOfDay'
# 'mileageSinceLastCharge'
# 'powerUsageOfDay'
# 'powerUsageSinceLastCharge'
# 'realtimePower'
# 'startTime'
# 'staticEnergyConsumption'
# 'totalBatteryCapacity'
# 'workingCurrent'
# 'workingVoltage'

        return False


