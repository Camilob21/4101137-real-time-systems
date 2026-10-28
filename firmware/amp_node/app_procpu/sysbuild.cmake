# The APPCPU image builds first: PROCPU's image needs its load address.
ExternalZephyrProject_Add(
	APPLICATION app_appcpu
	SOURCE_DIR ${APP_DIR}/../app_appcpu
	BOARD esp32s3_devkitc/esp32s3/appcpu
)
add_dependencies(app_procpu app_appcpu)
sysbuild_add_dependencies(CONFIGURE app_procpu app_appcpu)

if(SB_CONFIG_BOOTLOADER_MCUBOOT)
	sysbuild_add_dependencies(FLASH app_appcpu mcuboot)
endif()
