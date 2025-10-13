cmake_minimum_required(VERSION 3.16)
project(mouse-piper VERSION 1.0.0 LANGUAGES NONE)

set(CPACK_GENERATOR "DEB;TGZ")
set(CPACK_PACKAGE_NAME "mouse-piper")
set(CPACK_PACKAGE_VENDOR "Ivan Perehiniak")
set(CPACK_PACKAGE_CONTACT "Ivan Perehiniak")
set(CPACK_PACKAGE_VERSION "1.0.0")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "MousePiper — tool for adding functions to mouse buttons.")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Ivan Perehiniak")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3 (>= 3.6)")
set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_SOURCE_DIR}/postinst")
set(CPACK_PACKAGE_HOMEPAGE "https://github.com/perehinik/mouse-piper")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_CHANGELOG "${CMAKE_SOURCE_DIR}/CHANGELOG.md")
set(CPACK_DEBIAN_PACKAGE_DESCRIPTION
"Mouse Piper is a small Python-based service that captures and processes mouse signals.\n"
"\n"
"Features:\n"
" - Low-level mouse event collection\n"
" - Control hooks and signal routing\n"
" - Optional systemd auto-start on Debian systems\n"
)

install(
    DIRECTORY mp-lib/
    DESTINATION "lib/mouse-piper/"
    PATTERN "__pycache__" EXCLUDE
)
install(
    FILES mouse-piper.py
    DESTINATION "lib/mouse-piper/"
)
install(
    PROGRAMS mouse-piper
    DESTINATION "bin/"
)
install(
    FILES mouse-piper.service
    DESTINATION "lib/systemd/system/"
)

include(CPack)
