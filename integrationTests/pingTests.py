
# -*- coding: utf-8 -*-

import subprocess
import json
import sys, getopt
from pingAgent import Agent 
import formatHTML
import time

class main():
   
   def __init__(self,agentIPpath,testMode):
      self.agentIPpath = agentIPpath      
      if testMode == "remote": self.localHostName = "Nodemanager"
      elif testMode == "local": self.localHostName = "Client"      
      
      ## TO DO: get Nodemanager IP
      self.localHostIP = ""
      
      self.nodes = self.getNodes(agentIPpath)      
      formatHTML.setHTMLheader()
      self.pingAll()
   
   def getNodes(self,agentIPpath):
      with open(agentIPpath, 'r') as f:
         return json.load(f)

   def pingNode(self,ip):
      proc = subprocess.Popen(
         "ping -c 1 -w 1 " + ip,
         shell=True,
         stdout=subprocess.PIPE,
         stderr=subprocess.PIPE
      )
      result = proc.stdout.readlines()
      if result == []:
         error = proc.stderr.readlines()
         self.printLine("error",["Error: " + str(error)])
      else:		
         ResultsTmp = result[3].replace("\n","")         
         if ResultsTmp[0:2] == "--": ResultsTmp = result[4].replace("\n","")         
         valsArr = ResultsTmp.split(", ")
         valsOut = []
         for vals in valsArr:
            valsTmp = vals.split(" ")
            if valsTmp[0] != "+1":
               if valsTmp[0] == "time": valsOut.append(valsTmp[1])
               else: valsOut.append(valsTmp[0])
         self.printLine("row",valsOut)
   
   def printLine(self,style,vals,newLine = True):
      if testMode == "remote" : formatHTML.printPingTable(style,vals,newLine)
      elif testMode == "local" : self.printToShell(style,vals)
      
   def printToShell(self,style):
      print "test"
      # ----- TO DO ------
      # use Tabulate
   
   def pingAll(self):
      # pings from LocalHost to all Nodes
      # LocalHost can be either the Client or Nodemanager
      self.pingFromLocal()      
      self.pingAllToAll()
    
   def printTableHeader(self):
      self.printLine("header1",["From","To","Results"])
      self.printLine("header2",["Name","IP","Name","IP","Packets","Received","Loss","Delay"])
   
   def pingFromLocal(self):
      sys.stdout.flush()      
      self.printLine("headline",["Pinging created nodes from " + self.localHostName + "..."])
      self.printTableHeader()
      for nodename in self.nodes.keys(): 
         self.printLine("row",[self.localHostName,self.localHostIP],newLine = False)
         self.printNodeLine(self.nodes,nodename)
         sys.stdout.flush()
         if testMode == "local": self.pingNode(self.nodes[nodename]["public_addr"])
         #elif testMode == "remote": self.pingNode(self.getLocalIP(self.nodes[nodename]))
         elif testMode == "remote": self.pingNode(self.nodes[nodename]["mgmt"]["addr"])
      sys.stdout.flush()
   
   def printNodeLine(self,nodeObj,nodename):
      if testMode == "local": ip = nodeObj[nodename]["public_addr"]
      #elif testMode == "remote": ip = nodeObj[nodename]["mgmt"]["addr"]
      elif testMode == "remote": ip = self.getLocalIP(nodeObj[nodename])
      self.printLine("row",[nodename,ip],newLine = False)
   
   def getLocalIP(self,nodeDict):
      for key in nodeDict.keys():
         if (key != "public_addr" and key != "mgmt"):
            return nodeDict[key]["addr"]
   
   def pingAllToAll(self):
      agents = Agent(self.nodes)
      agents.addHostsToNodes()
      sys.stdout.flush()
      self.printLine("headline",["Pinging all nodes to other..."])
      self.printTableHeader()
      for srcNode in agents.nodes:
            for dstNode in agents.createHostsList(srcNode,"list"):
               self.printNodeLine(agents.nodes,srcNode)
               self.printNodeLine(agents.nodes,dstNode)
               try:
                  res = agents.pingTo(srcNode,dstNode).json()
                  #print res
                  time.sleep(1)
                  res = res[res.keys()[0]]
                  packets = res[res.keys()[4]]
                  received = res[res.keys()[2]]
                  loss = res[res.keys()[1]]
                  delay = res[res.keys()[10]]
                  self.printLine("row",[packets,received,loss,delay])                    
               except Exception, e:
                  self.printLine("error",["connection Failed." + str(e)[0:50]])

if __name__ == "__main__":
   agentIPpath = "/opt/MockFog/iac/created/agentIPs.json"
   testMode = "remote"
   argv = sys.argv[1:]
   try:
      opts, args = getopt.getopt(argv,"hf:o:")
   except getopt.GetoptError:
      print 'Wrong Argument. Use PingTest.py -f </path/to/agentIP.json> -t [local/remote]'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print "PingTest.py -f </path/to/agentIP.json>",
         print "Defaults are: AgentIPs:" + agentIPpath + " testMode: " + testMode
         sys.exit()
      elif opt in ("-f"): agentIPpath = arg
      elif opt in ("-t"): testMode = arg
      
   if agentIPpath == "" :
      print "please select path with -i </path/to/AgentIPs.json>"
      sys.exit(2)
   if testMode != "remote" and testMode != "local":
      print "please select correct test mode with -t [local/remote]"
      
   main(agentIPpath,testMode)
