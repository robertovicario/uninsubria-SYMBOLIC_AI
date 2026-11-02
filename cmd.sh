#!/bin/bash

# =========================
# Configurations
# =========================

# Icons
ICON_START="▶"     # U+25B6
ICON_STOP="■"      # U+25A0
ICON_SETUP="⚙"     # U+2699
ICON_DOWNLOAD="↓"  # U+2193
ICON_CLEAN="♻"     # U+267B
ICON_OK="✓"        # U+2713
ICON_ERR="✗"       # U+2717

# Colors
RESET="\033[0m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"

# =========================
# Methods
# =========================

setup() {

    # Environment
    printer -setup "Set up the project..."
    git submodule update --init --recursive

    # Handler
    local STATUS=$?
    handler "$STATUS"
}

notes() {

    printer -start "Generating the notes..."
    mkdir -p dist
    FILES=()
    while IFS= read -r f; do
        FILES+=("$f")
    done < <(printf "%s\n" md/notes/*.md | sort -V)
    pandoc "${FILES[@]}" \
        -o dist/content-1.pdf \
        --metadata-file=md/__metadata__.yml \
        --from=markdown \
        --template=pandoc-latex-template/template-multi-file/eisvogel.latex \
        --pdf-engine=xelatex \
        --filter=pandoc-latex-environment \
        --syntax-highlighting=idiomatic

    local STATUS=$?
    if [ "$STATUS" -eq 0 ]; then
        pdfunite \
            dist/front-1.pdf \
            dist/content-1.pdf \
            dist/Notes.pdf

        STATUS=$?
    fi
    if [ "$STATUS" -eq 0 ]; then
        open dist/
        STATUS=$?
    fi

    # Handler
    handler "$STATUS"
}

project() {

    printer -start "Generating the project work..."
    mkdir -p dist
    FILES=()
    while IFS= read -r f; do
        FILES+=("$f")
    done < <(printf "%s\n" md/project/*.md | sort -V)
    pandoc "${FILES[@]}" \
        -o dist/content-2.pdf \
        --metadata-file=md/__metadata__.yml \
        --from=markdown \
        --template=pandoc-latex-template/template-multi-file/eisvogel.latex \
        --pdf-engine=xelatex \
        --filter=pandoc-latex-environment \
        --syntax-highlighting=idiomatic

    local STATUS=$?
    if [ "$STATUS" -eq 0 ]; then
        pdfunite \
            dist/front-2.pdf \
            dist/content-2.pdf \
            dist/Project-Work.pdf

        STATUS=$?
    fi
    if [ "$STATUS" -eq 0 ]; then
        open dist/
        STATUS=$?
    fi

    # Handler
    handler "$STATUS"
}

# =========================
# Handlers
# =========================

usage() {

    # Operations
    cat <<EOF

1. Usage:
    - bash $0 <command>

2. Commands:
    - [${ICON_START}] notes
    - [${ICON_START}] project
    - [${ICON_SETUP}] setup

EOF
    exit 1
}

printer() {

    # Operations
    local STATUS="$1"
    local MESSAGE="$2"
    local ICON=""
    local COLOR=""
    case "$STATUS" in
        -start)
            ICON="$ICON_START"
            COLOR="$BLUE"
            ;;
        -stop)
            ICON="$ICON_STOP"
            COLOR="$RED"
            ;;
        -debug)
            ICON="$ICON_START"
            COLOR="$CYAN"
            ;;
        -setup)
            ICON="$ICON_SETUP"
            COLOR="$MAGENTA"
            ;;
        -clean)
            ICON="$ICON_CLEAN"
            COLOR="$YELLOW"
            ;;
        -success)
            ICON="$ICON_OK"
            COLOR="$GREEN"
            ;;
        -error)
            ICON="$ICON_ERR"
            COLOR="$RED"
            ;;
        *)
            ICON="$ICON_ERR"
            COLOR="$RED"
            ;;
    esac
    echo ""
    echo -e "${COLOR}[${ICON}] ${MESSAGE}${RESET}"
    echo ""
}

handler() {

    # Operations
    local STATUS=$1
    if [ $STATUS -eq 0 ]; then
        printer -success "Process completed successfully"
    else
        printer -error "An unexpected error occurred"
        exit 1
    fi
}

case $1 in
    notes)
        notes
        ;;
    project)
        project
        ;;
    setup)
        setup
        ;;
    *)
        usage
        ;;
esac

# -------------------------
