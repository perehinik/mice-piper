cmake_minimum_required(VERSION 3.16)
project(mice-piper VERSION 1.0.1 LANGUAGES NONE)

set(CPACK_GENERATOR "DEB;TGZ")
set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
set(CPACK_PACKAGE_VENDOR "Ivan Perehiniak")
set(CPACK_PACKAGE_CONTACT "Ivan Perehiniak")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Mice Piper — tool for adding functions to mouse buttons.")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Ivan Perehiniak")
set(CPACK_DEBIAN_PACKAGE_SECTION "utils")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3 (>= 3.6)")
set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
    "${CMAKE_SOURCE_DIR}/debian/postinst"
    "${CMAKE_SOURCE_DIR}/debian/prerm"
)
set(CPACK_PACKAGE_HOMEPAGE "https://github.com/perehinik/mice-piper")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_CHANGELOG "${CMAKE_SOURCE_DIR}/CHANGELOG.md")
set(CPACK_DEBIAN_PACKAGE_DESCRIPTION
"Mice Piper is a small Python-based service that captures and processes mouse signals.\n"
"\n"
"Features:\n"
" - Low-level mouse event collection\n"
" - Control hooks and signal routing\n"
" - Optional systemd auto-start on Debian systems\n"
)

install(
    DIRECTORY mp-lib/
    DESTINATION "lib/mice-piper/"
    PATTERN "__pycache__" EXCLUDE
)
install(
    FILES
        mice-piper.py
        piper_actions.py
        piper_device.py
    DESTINATION "lib/mice-piper/"
)
install(
    PROGRAMS mice-piper
    DESTINATION "bin/"
)
install(
    FILES mice-piper.service
    DESTINATION "lib/systemd/system/"
)

include(CPack)
