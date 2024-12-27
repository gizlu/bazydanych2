package main

// based on https://github.com/charmbracelet/wish/blob/main/examples/exec/main.go

import (
	"context"
	"errors"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/charmbracelet/log"
	"github.com/charmbracelet/ssh"
	"github.com/charmbracelet/wish"
	"github.com/charmbracelet/wish/activeterm"
	"github.com/charmbracelet/wish/logging"
)

const (
	host = "localhost"
	port = "23234"
	execpath = "/home/gizlu/Dev/studia/języki_programowania/poprawka/lab3/out/production/lab3/launch_zad1.sh"
)

func main() {
	if(len(os.Args) != 4) {
		println("usage: prog host port path-to-exec");
		println("example: ./serve localhost 23234 $(pwd)/main.py");
		os.Exit(0);
	}
	var (
		host = os.Args[1]
		port = os.Args[2]
		execpath = os.Args[3]
	)
	s, err := wish.NewServer(
		wish.WithAddress(net.JoinHostPort(host, port)),

		// Allocate a pty.
		// This creates a pseudoconsole on windows, compatibility is limited in
		// that case, see the open issues for more details.
		ssh.AllocatePty(),
		wish.WithMiddleware(
			func(next ssh.Handler) ssh.Handler {
				return func(s ssh.Session) {
					// wish.Co
					cmd := wish.Command(s, execpath)
					if err := cmd.Run(); err != nil {
						wish.Fatalln(s, err)
					}
					next(s)
				}
			},
			// ensure the user has requested a tty
			activeterm.Middleware(),
			logging.Middleware(),
		),
	)
	if err != nil {
		log.Error("Could not start server", "error", err)
	}

	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	log.Info("Starting SSH server", "host", host, "port", port)
	go func() {
		if err = s.ListenAndServe(); err != nil && !errors.Is(err, ssh.ErrServerClosed) {
			log.Error("Could not start server", "error", err)
			done <- nil
		}
	}()

	<-done
	log.Info("Stopping SSH server")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer func() { cancel() }()
	if err := s.Shutdown(ctx); err != nil && !errors.Is(err, ssh.ErrServerClosed) {
		log.Error("Could not stop server", "error", err)
	}
}
