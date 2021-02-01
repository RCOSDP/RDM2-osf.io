<div id="${addon_short_name}Scope" class="scripted" >
    <div>
        <!-- Add credentials modal -->
        <%include file="integromat_credentials_modal.mako"/>

        <h4 class="addon-title">
            <img class="addon-icon" src=${addon_icon_url}>
            ${addon_full_name}

            <small class="authorized-by">
                % if node_has_auth:
                        authorized by
                        <a href="${auth_osf_url}" target="_blank">
                        ${auth_osf_name}
                        </a>
                    % if not is_registration:
                        <a id="integromatRemoveToken" class="text-danger pull-right addon-auth" >
                          Disconnect Account
                        </a>
                    % endif
                % else:
                    % if user_has_auth:
                        <a id="integromatImportToken" class="text-primary pull-right addon-auth">
                           Import Account from Profile
                        </a>
                    % else:
                        <a href="#integromatCredentialsModal" data-toggle="modal" class="text-primary pull-right addon-auth">
                           Connect Account
                        </a>
                    % endif
                % endif
            </small>
        </h4>
    </div>

    % if node_has_auth and valid_credentials:

        <div align="right">
            <i title="Manage your Microsoft User information to create meetings." class="fa fa-question-circle text-muted"></i>
            <a href="#microsoftTeamsUserRegistrationModal" data-toggle="modal"
            class="btn btn-primary" style="margin-bottom:10px">
            Manage Microsoft Teams Attendees
            </a>
        </div>
        <div id="scenarioList" ></div>
        <table width="100%" border="1" bordercolor="#f0f8ff">
            <th>
            <div class="tb-row-titles">
                <div style="width: 75%" data-tb-th-col="0" class="tb-th">
                    <span class="m-r-sm">Scenario Name</span>
                </div>
            </div>
            </th>
            <th>
            <div class="tb-row-titles">
                <div style="width: 75%" data-tb-th-col="1" class="tb-th">
                    <span class="m-r-sm">Activate / Deactivate</span>
                </div>
            </div>
            </th>
            </table>

    % endif
</div>