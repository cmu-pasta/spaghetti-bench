#!/usr/bin/env bash

javac UnhandledExceptionReporterAgent.java
jar cmf MANIFEST.MF UnhandledExceptionReporterAgent.jar *.class
