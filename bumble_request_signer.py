from burp import IBurpExtender, IHttpListener
import hashlib


class BurpExtender(IBurpExtender, IHttpListener):
    def registerExtenderCallbacks(self, callbacks):
        # Obtain an extension helpers object
        self._helpers = callbacks.getHelpers()
        self._callbacks = callbacks

        # Set our extension name
        callbacks.setExtensionName('Bumble Request Signer')

        # Register ourselves as an HTTP listener
        callbacks.registerHttpListener(self)

    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        # Only process requests from the Repeater or Intruder.
        if not messageIsRequest:
            return

        if toolFlag != self._callbacks.TOOL_REPEATER and toolFlag != self._callbacks.TOOL_INTRUDER:
            return

        # Get the host for this request.
        host = messageInfo.getHttpService().getHost()

        if host.endswith('.bumble.com') or host == 'bumble.com':
            request = messageInfo.getRequest()
            requestInfo = self._helpers.analyzeRequest(request)
            headers = requestInfo.getHeaders()
            body = self._helpers.bytesToString(request[requestInfo.getBodyOffset():])

            # Iterate over the headers to find which header to replace (if any)
            replaced = False
            for idx in range(len(headers)):
                if headers[idx].startswith('X-Pingback: '):
                    headers[idx] = 'X-Pingback: ' + self.computeSignature(body)
                    replaced = True

            if not replaced:
                headers.add('X-Pingback: ' + self.computeSignature(body))

            # Update the request in Burp
            updatedRequest = self._helpers.buildHttpMessage(headers, body)
            messageInfo.setRequest(updatedRequest)

    def computeSignature(self, body):
        text = body + 'whitetelevisionbulbelectionroofhorseflying'
        return hashlib.md5(text.encode()).hexdigest()
