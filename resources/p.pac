function FindProxyForURL(url, host) {
  if (shExpMatch(host, "www.handyfeeling.com")) {
    if (shExpMatch(url, "*api/handy/v2/servertime*")) {
      return "DIRECT";  // Bypass proxy for this specific path
    }
    return "PROXY 127.0.0.1:8080";  // Use proxy for all other paths
  }
  return "DIRECT";  // Bypass proxy for all other hosts
}
