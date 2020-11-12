package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"syscall"

	"aws-lambda-extensions/aoc-extension/extension"
)

var (
	extensionName   = filepath.Base(os.Args[0]) // extension name has to match the filename
	extensionClient = extension.NewClient(os.Getenv("AWS_LAMBDA_RUNTIME_API"))
	printPrefix     = fmt.Sprintf("[%s]", extensionName)
	otelCol         = "/opt/otelcol/collector"
	otelColCfg      = "/opt/otelcol/config.yaml"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		s := <-sigs
		cancel()
		println(printPrefix, "Received", s)
		println(printPrefix, "Exiting")
	}()

	// configKeys are keys requested from Extensions configuration during /register defined in the API docs
	configKeys := []string{"FOO"}
	res, err := extensionClient.Register(ctx, extensionName, configKeys)
	if err != nil {
		panic(err)
	}
	println(printPrefix, "Register response:", prettyPrint(res))

	// launch AOC
	println("Launching aoc...")
	cmd := exec.Command(otelCol, "--config",  otelColCfg, "--log-level=DEBUG")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Start()
	if err != nil {
		println("aoc launch failed")
		panic(err)
	}
    // TODO: ping /health to make sure aoc is ready
	println("aoc is ready.")

	// Will block until shutdown event is received or cancelled via the context.
	processEvents(ctx)
}

func processEvents(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
			println(printPrefix, "Waiting for event...")
			res, err := extensionClient.NextEvent(ctx)
			if err != nil {
				println(printPrefix, "Error:", err)
				println(printPrefix, "Exiting")
				return
			}
			println(printPrefix, "Received event:", prettyPrint(res))
			// TODO: aoc health check

			// Exit if we receive a SHUTDOWN event
			if res.EventType == extension.Shutdown {
				println(printPrefix, "Received SHUTDOWN event")
				//TODO: shutdown aoc
				println(printPrefix, "Exiting")
				return
			}
		}
	}
}

func prettyPrint(v interface{}) string {
	data, err := json.MarshalIndent(v, "", "\t")
	if err != nil {
		return ""
	}
	return string(data)
}
