// Copyright 2016 VMware, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

// A VMDK Docker Data Volume plugin - main
// relies on docker/go-plugins-helpers/volume API

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	log "github.com/Sirupsen/logrus"
	"github.com/docker/go-plugins-helpers/volume"
	"github.com/natefinch/lumberjack"
	"github.com/vmware/docker-volume-vsphere/vmdk_plugin/drivers/photon"
	"github.com/vmware/docker-volume-vsphere/vmdk_plugin/drivers/vmdk"
	"github.com/vmware/docker-volume-vsphere/vmdk_plugin/utils/config"
)

const (
	pluginSockDir = "/run/docker/plugins"
	mountRoot     = "/mnt/vmdk" // VMDK and photon volumes are mounted here
	photonDriver  = "photon"
	vmdkDriver    = "vmdk"
)

// An equivalent function is not exported from the SDK.
// API supports passing a full address instead of just name.
// Using the full path during creation and deletion. The path
// is the same as the one generated internally. Ideally SDK
// should have ability to clean up sock file instead of replicating
// it here.
func fullSocketAddress(pluginName string) string {
	return filepath.Join(pluginSockDir, pluginName+".sock")
}

// init log with passed logLevel (and get config from configFile if it's present)
// returns True if using defaults,  False if using config file
func logInit(logLevel *string, logFile *string, configFile *string) bool {
	level, err := log.ParseLevel(*logLevel)
	if err != nil {
		panic(fmt.Sprintf("Failed to parse log level: %v", err))
	}

	usingConfigDefaults := false
	c, err := config.Load(*configFile)
	if err != nil {
		if os.IsNotExist(err) {
			usingConfigDefaults = true // no .conf file, so using defaults
			c = config.Config{}
			config.SetDefaults(&c)
		} else {
			panic(fmt.Sprintf("Failed to load config file %s: %v",
				*configFile, err))
		}
	}

	path := c.LogPath
	if logFile != nil {
		path = *logFile
	}
	log.SetOutput(&lumberjack.Logger{
		Filename: path,
		MaxSize:  c.MaxLogSizeMb,  // megabytes
		MaxAge:   c.MaxLogAgeDays, // days
	})

	log.SetFormatter(new(VmwareFormatter))
	log.SetLevel(level)

	if usingConfigDefaults {
		log.Info("No config file found. Using defaults.")
	}
	return usingConfigDefaults
}

// main for docker-volume-vsphere
// Parses flags, initializes and mounts refcounters and finally services Docker requests
func main() {
	var driver volume.Driver

	// Define command line options
	driverName := flag.String("driver", "vmdk", "Volume driver")
	logLevel := flag.String("log_level", "debug", "Logging Level")
	configFile := flag.String("config", config.DefaultConfigPath, "Configuration file path")

	// photon driver options
	targetURL := flag.String("target", "", "Photon controller URL")
	projectID := flag.String("project", "", "Project ID of the docker host")
	vmID := flag.String("host", "", "ID of docker host")

	// vmdk driver options
	port := flag.Int("port", 1019, "Default port to connect to ESX service")
	useMockEsx := flag.Bool("mock_esx", false, "Mock the ESX service")

	flag.Parse()

	logInit(logLevel, nil, configFile)

	log.WithFields(log.Fields{
		"driver":    *driverName,
		"log_level": *logLevel,
		"config":    *configFile,
	}).Info("Starting plugin ")

	log.WithFields(log.Fields{
		"target":  *targetURL,
		"project": *projectID,
		"host":    *vmID,
		"port":    *port}).Info("Plugin options - ")

	if *driverName == photonDriver {
		driver = photon.NewVolumeDriver(*targetURL, *projectID,
			*vmID, mountRoot)
	} else if *driverName == vmdkDriver {
		driver = vmdk.NewVolumeDriver(*port, *useMockEsx, mountRoot)
	} else {
		log.Warning("Unknown driver, exiting - ", *driverName)
		os.Exit(1)
	}

	sigChannel := make(chan os.Signal, 1)
	signal.Notify(sigChannel, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigChannel
		log.WithFields(log.Fields{"signal": sig}).Warning("Received signal ")
		os.Remove(fullSocketAddress(*driverName))
		os.Exit(0)
	}()

	handler := volume.NewHandler(driver)

	log.WithFields(log.Fields{
		"address": fullSocketAddress(*driverName),
	}).Info("Going into ServeUnix - Listening on Unix socket ")

	log.Info(handler.ServeUnix("root", fullSocketAddress(*driverName)))
}
