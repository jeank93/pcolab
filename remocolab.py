import pathlib, stat, shutil, urllib.request, subprocess, time
import json, sys
import os, tarfile


def _log(message):
	print("[%s] %s" % (time.strftime("%H:%M:%S", time.localtime()), message))

def _download(url, path):
	try:
		with urllib.request.urlopen(url) as response:
			with open(path, "wb") as outfile:
				shutil.copyfileobj(response, outfile)
	except:
		print("Failed to download ", url)
		raise

def _setupSSHD(region, token):
	_log("Downloading and installing ngrok...")
	_download("https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip", "ngrok.zip")
	shutil.unpack_archive("ngrok.zip")
	pathlib.Path("ngrok").chmod(stat.S_IXUSR)
	
	if not pathlib.Path("/root/.ngrok2/ngrok.yml").exists():
		subprocess.run(["./ngrok", "authtoken", token])
	
	_log("Creating ngrok tunnel...")
	ngrok_proc = subprocess.Popen(["./ngrok", "tcp", "-region", region, "1080"])
	time.sleep(2)
	if ngrok_proc.poll() != None:
		raise RuntimeError("Failed to run ngrok. Return code:" + str(ngrok_proc.returncode) + "\nSee runtime log for more info.")
	
	with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
		url = json.load(response)["tunnels"][0]["public_url"]
		if url.startswith("tcp://"):
			url = url[len("tcp://"):]
	
	return url

def _setupProxy(url):
	proxy3_ver = "0.8.13"
	
	proxy3_url = "https://github.com/z3APA3A/3proxy/archive/{0}.tar.gz".format(proxy3_ver)
	
	proxy3_dir = "3proxy-{0}".format(proxy3_ver)
	proxy3_makefile = "Makefile.Linux"
	proxy3_cfgdir = "/usr/local/etc/3proxy"
	proxy3_cfgfile = os.path.join(proxy3_cfgdir, "3proxy.cfg")
	
	_log("Downloading and installing 3proxy...")
	_download(proxy3_url, "3proxy.tar.gz")
	tar = tarfile.open("3proxy.tar.gz", "r:gz")
	tar.extractall()
	tar.close()
	subprocess.run(["make", "-C", proxy3_dir, "-f", proxy3_makefile])
	subprocess.run(["make", "-C", proxy3_dir, "-f", proxy3_makefile, "install"])
	pathlib.Path(proxy3_cfgdir).mkdir(parents=True, exist_ok=True)
	with open(proxy3_cfgfile, "w+") as f:
		proxy_config = [
			"nserver 8.8.8.8",
			"daemon",
			"auth none",
			"external 0.0.0.0",
			"internal 0.0.0.0",
			"flush",
			"socks -aunp1080"
		]
		f.write("\n".join(proxy_config))
		f.close()
	
	_log("Running the proxy server...")
	subprocess.run(["3proxy", proxy3_cfgfile])
	
	_log("Ready!")
	index = url.find(":")
	print("Protocol: SOCKS5")
	if index != -1:
		print("Server: {0}".format(url[:index]))
		print("Port: {0}".format(url[index+1:]))
	else:
		print("Server: {0}".format(url))

def setupProxy(region="", token=None):
	if not token:
		sys.exit("ERROR: Invalid ngrok authtoken. Ensure you have copied the token from https://dashboard.ngrok.com/auth and try again.")
	
	index = region.find(" ")
	if index != -1:
		region = region[:index]
	
	_log("Starting...")
	url = _setupSSHD(region, token)
	_setupProxy(url)
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		_log("Exiting...")
