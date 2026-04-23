def convertIP2EnclosedAlphanumericsValue():
	IPAddressParts4EnclosedAlphanumerics = arg1.split(".")
	returnEnclosedAlphanumericsIPAddress = ""
	for x in range(0,4):
		if len(IPAddressParts4EnclosedAlphanumerics[x]) == 3 and (int(IPAddressParts4EnclosedAlphanumerics[x][0]+IPAddressParts4EnclosedAlphanumerics[x][1])) <= 20 and (int(IPAddressParts4EnclosedAlphanumerics[x][0]+IPAddressParts4EnclosedAlphanumerics[x][1]+IPAddressParts4EnclosedAlphanumerics[x][2])) >= 10:
			returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar(IPAddressParts4EnclosedAlphanumerics[x][0]+IPAddressParts4EnclosedAlphanumerics[x][1]);
			returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar(IPAddressParts4EnclosedAlphanumerics[x][2]);
			if x <= 2:
				returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar('.');
		else:
			returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar(IPAddressParts4EnclosedAlphanumerics[x][0]);
			if len(IPAddressParts4EnclosedAlphanumerics[x]) >= 2:
				returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar(IPAddressParts4EnclosedAlphanumerics[x][1]);
			if len(IPAddressParts4EnclosedAlphanumerics[x]) == 3:
				returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar(IPAddressParts4EnclosedAlphanumerics[x][2]);
			if x <= 2:
				returnEnclosedAlphanumericsIPAddress = returnEnclosedAlphanumericsIPAddress + plain2EnclosedAlphanumericsChar('.');
	return returnEnclosedAlphanumericsIPAddress