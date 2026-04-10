from stixdcpy.net import Request

stix_lc = Request.fetch_light_curves("2021-05-22 16:04:34", "2021-05-22 16:41:34", ltc=False)

print(stix_lc.keys())